"""
solution_agent.py
─────────────────
Uses Google Gemini to:
  1. Generate a correct C++ solution with explanation
  2. Extract the code block (STEP 12)
  3. Compile / syntax-check the code (STEP 13)
  4. Run sample test cases and verify output (STEP 14)
"""

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential
from groq import Groq
from logger import log

load_dotenv()

# ── Gemini setup ───────────────────────────────────────────────────────────────
# _client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY_SOLUTION", "dummy"))
# GEMINI_MODEL = "gemini-2.0-flash-lite"
# ── GROQ setup ───────────────────────────────────────────────────────────────
_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


SOLUTION_PROMPT = """\
Solve this LeetCode problem in C++.

Problem: {title} ({difficulty})
{description}

Starter code:
```cpp
{starter_code}
```

Return:
1. Complete C++ solution in a ```cpp``` block using the exact class/method signature.
2. After the block, provide:
   - Intuition: explain the core insight in 2-3 sentences as if talking to a beginner
   - Approach: step-by-step algorithm in plain English
   - Time Complexity: O(?) with explanation
   - Space Complexity: O(?) with explanation
Be thorough in the explanation but concise in the code."""


VERIFY_PROMPT = """\
The following C++ solution for "{title}" failed during testing:

```cpp
{code}
```

Error / Wrong output:
{error}

Please fix the solution. Return ONLY the corrected ```cpp``` code block, nothing else.
"""


# ── STEP 2: Extract code block ────────────────────────────────────────────────
def extract_code(text: str) -> str:
    """Pull the first ```cpp ... ``` or ```python ... ``` block."""
    pattern = r"```(?:cpp|c\+\+|python)?\s*\n([\s\S]*?)```"
    matches = re.findall(pattern, text)
    if not matches:
        raise ValueError("No code block found in model response")
    return matches[0].strip()


# ── STEP 13: Compile / syntax-check ───────────────────────────────────────────
def compile_check(code: str) -> None:
    """Basic sanity check for C++ code."""
    if not code or len(code.strip()) < 10:
        raise ValueError("Generated code block is empty or too short")
    if "class Solution" not in code and "int main" not in code:
        raise ValueError("Generated code doesn't look like a valid C++ solution")
    log.info("✓ Syntax check passed")


# ── STEP 2: Run sample test cases ────────────────────────────────────────────
def build_test_harness(code: str, problem: dict, language: str = "cpp") -> str:
    """
    Wrap solution code in a minimal smoke-test harness.

    Supports:
    - C++
    - Python
    """

    # ───────────────────────────────────────────────────────────
    # PYTHON HARNESS
    # ───────────────────────────────────────────────────────────
    if language.lower() in ["python","python3"]:

        # Extract class name
        class_match = re.search(r"class\s+(\w+)", code)
        class_name = class_match.group(1) if class_match else "Solution"

        # Extract method name
        method_match = re.search(r"def\s+(\w+)\s*\(\s*self", code)
        method_name = method_match.group(1) if method_match else "unknown_method"

        harness = textwrap.dedent(f"""\
            {code}

            # ── Auto-generated smoke test ──────────────────────
            import traceback

            try:
                sol = {class_name}()
                print("Solution instantiated successfully")
                print("Method detected: {method_name}")
                print("SMOKE_TEST_PASSED")

            except Exception as e:
                print("SMOKE_TEST_FAILED")
                traceback.print_exc()
        """)

        return harness

    # ───────────────────────────────────────────────────────────
    # C++ HARNESS
    # ───────────────────────────────────────────────────────────
    elif language.lower() in ["cpp", "c++"]:

        # Extract class name
        class_match = re.search(r"class\s+(\w+)", code)
        class_name = class_match.group(1) if class_match else "Solution"

        harness = textwrap.dedent(f"""\
            #include <bits/stdc++.h>
            using namespace std;

            {code}

            // ── Auto-generated smoke test ──────────────────────
            int main() {{
                try {{
                    {class_name} sol;

                    cout << "Solution instantiated successfully" << endl;
                    cout << "SMOKE_TEST_PASSED" << endl;

                }} catch (...) {{
                    cout << "SMOKE_TEST_FAILED" << endl;
                }}

                return 0;
            }}
        """)

        return harness

    # ───────────────────────────────────────────────────────────
    # UNKNOWN LANGUAGE
    # ───────────────────────────────────────────────────────────
    else:
        raise ValueError(f"Unsupported language: {language}")


def run_code(code: str, problem: dict, timeout: int = 10) -> tuple[bool, str]:
    """Execute the test harness in a subprocess. Returns (passed, output)."""
    harness = build_test_harness(code, problem, "cpp")

    with tempfile.NamedTemporaryFile(suffix=".cpp", mode="w", delete=False, encoding="utf-8") as f:
        f.write(harness)
        tmp_path = f.name

    exe_path = tmp_path.replace(".cpp", "")
    
    try:
        compile_result = subprocess.run(
            ["g++", tmp_path, "-o", exe_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if compile_result.returncode != 0:
            return False, compile_result.stderr

        result = subprocess.run(
            [exe_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = result.stdout + result.stderr

        passed = (
            result.returncode == 0
            and "SMOKE_TEST_PASSED" in output
        )

        return passed, output

    except subprocess.TimeoutExpired:
        return False, "TimeoutError: Code ran too long"

    finally:
        Path(tmp_path).unlink(missing_ok=True)
        Path(exe_path).unlink(missing_ok=True)


# ── Main agent ─────────────────────────────────────────────────────────────────
# retry removed — pipeline.py already retries the full step
# def _call_gemini(prompt: str) -> str:
#     response = _client.models.generate_content(
#         model=GEMINI_MODEL,
#         contents=prompt,
#         config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=1024),
#     )
#     return response.text

def _call_groq(prompt: str) -> str:
    response = _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
    )
    return response.choices[0].message.content


def generate_solution(problem: dict, max_fix_attempts: int = 1) -> dict:
    """
    Full pipeline:
      generate → extract → compile-check → run → (fix loop) → return
    """
    log.info(f"Generating solution for: {problem['title']} …")

    cpp_starter = problem.get("starter_code_cpp") or problem["starter_code"]

    prompt = SOLUTION_PROMPT.format(
        title=problem["title"],
        difficulty=problem["difficulty"],
        
        description=problem["description"],
        starter_code=cpp_starter,
    )

    raw_response = _call_groq(prompt)
    code = extract_code(raw_response)
    compile_check(code)

    # Separate explanation from raw response
    explanation = re.sub(r"```[\s\S]*?```", "", raw_response).strip()

    # Test execution
    passed, run_output = run_code(code, problem)
    log.info(f"Initial run: {'✓ passed' if passed else '✗ failed'}")

    # Fix loop
    for attempt in range(max_fix_attempts):
        if passed:
            break
        log.warning(f"Fix attempt {attempt + 1}/{max_fix_attempts} …")
        fix_prompt = VERIFY_PROMPT.format(
            title=problem["title"],
            code=code,
            error=run_output[:1000],
        )
        fix_response = _call_groq(fix_prompt).strip()
        try:
            code = extract_code(fix_response)
            compile_check(code)
            passed, run_output = run_code(code, problem)
            log.info(f"After fix {attempt+1}: {'✓ passed' if passed else '✗ failed'}")
        except Exception as e:
            log.error(f"Fix attempt failed: {e}")

    result = {
        "code": code,
        "explanation": explanation,
        "full_response": raw_response,
        "test_passed": passed,
        "test_output": run_output,
    }

    log.info(f"Solution generation complete. Tests passed: {passed}")
    return result


def save_solution(solution: dict, problem: dict, out_dir: str = "output") -> Path:
    """Save code + explanation to disk."""
    base = Path(out_dir)
    base.mkdir(parents=True, exist_ok=True)

    # Save raw CPP file
    code_path = base / "solution.cpp"
    code_path.write_text(solution["code"])

    # Save full JSON
    json_path = base / "solution.json"
    json_path.write_text(
        json.dumps(
            {
                "problem_id": problem["id"],
                "title": problem["title"],
                "difficulty": problem["difficulty"],
                "code": solution["code"],
                "explanation": solution["explanation"],
                "test_passed": solution["test_passed"],
                "test_output": solution["test_output"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )

    log.info(f"Saved solution → {code_path}")
    log.info(f"Saved solution JSON → {json_path}")
    return json_path


# ── CLI test ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    problem_path = Path("output/problem.json")
    if not problem_path.exists():
        print("Run fetch_potd.py first to generate output/problem.json")
        sys.exit(1)

    problem = json.loads(problem_path.read_text())
    solution = generate_solution(problem)
    save_solution(solution, problem)
    print("\n── Generated Code ──────────────────────────")
    print(solution["code"])
    print("\n── Explanation ─────────────────────────────")
    print(solution["explanation"])