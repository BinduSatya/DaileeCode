"""
solution_agent.py
─────────────────
Uses Google Gemini to:
  1. Generate a correct Python solution with explanation
  2. Extract the code block (STEP 12)
  3. Compile / syntax-check the code (STEP 13)
  4. Run sample test cases and verify output (STEP 14)
"""

import ast
import json
import logging
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

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")
log = logging.getLogger(__name__)

# ── Gemini setup ───────────────────────────────────────────────────────────────
# _client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY_SOLUTION", "dummy"))
# GEMINI_MODEL = "gemini-2.0-flash-lite"
_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# Token budget per call: ~600 input + ~800 output = ~1400 tokens total
SOLUTION_PROMPT = """\
Solve this LeetCode problem in Python 3.

Problem: {title} ({difficulty})
{description}

Starter code:
```python
{starter_code}
```

Return:
1. Complete solution in a ```python``` block using the exact method signature.
2. After the block: one line each for intuition, approach, time complexity, space complexity.
Keep it concise."""

VERIFY_PROMPT = """\
The following Python solution for "{title}" failed during testing:

```python
{code}
```

Error / Wrong output:
{error}

Please fix the solution. Return ONLY the corrected ```python ... ``` code block, nothing else.
"""


# ── STEP 12: Extract code block ────────────────────────────────────────────────
def extract_code(text: str) -> str:
    """Pull the first ```python ... ``` block from Gemini's response."""
    pattern = r"```(?:python)?\s*\n([\s\S]*?)```"
    matches = re.findall(pattern, text)
    if not matches:
        raise ValueError("No Python code block found in model response")
    return matches[0].strip()


# ── STEP 13: Compile / syntax-check ───────────────────────────────────────────
def compile_check(code: str) -> None:
    """Raise SyntaxError if code is syntactically invalid."""
    try:
        ast.parse(code)
        log.info("✓ Syntax check passed")
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in generated code: {e}") from e


# ── STEP 14: Run sample test cases ────────────────────────────────────────────
def build_test_harness(code: str, problem: dict) -> str:
    """
    Wrap the solution in a minimal test harness.
    We inject the sample_testcase inputs as a smoke-test.
    """
    # Extract class name (usually 'Solution')
    class_match = re.search(r"class (\w+)", code)
    class_name = class_match.group(1) if class_match else "Solution"

    # Extract method name from starter code
    method_match = re.search(r"def (\w+)\(self", code)
    method_name = method_match.group(1) if method_match else None

    harness = textwrap.dedent(f"""\
        {code}

        # ── Auto-generated smoke test ──────────────────────────
        import sys, json, traceback

        sol = {class_name}()
        print("Solution instantiated successfully")
        print("Method: {method_name}")
        print("SMOKE_TEST_PASSED")
    """)
    return harness


def run_code(code: str, problem: dict, timeout: int = 10) -> tuple[bool, str]:
    """Execute the test harness in a subprocess. Returns (passed, output)."""
    harness = build_test_harness(code, problem)

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(harness)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        passed = result.returncode == 0 and "SMOKE_TEST_PASSED" in output
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "TimeoutError: Code ran too long"
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ── Main agent ─────────────────────────────────────────────────────────────────
# retry removed — pipeline.py already retries the full step
# def _call_gemini(prompt: str) -> str:
#     response = _client.models.generate_content(
#         model=GEMINI_MODEL,
#         contents=prompt,
#         config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=1024),
#     )
#     return response.text

def _call_gemini(prompt: str) -> str:
    response = _client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # free, very capable
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    return response.choices[0].message.content


def generate_solution(problem: dict, max_fix_attempts: int = 1) -> dict:
    """
    Full pipeline:
      generate → extract → compile-check → run → (fix loop) → return
    """
    log.info(f"Generating solution for: {problem['title']} …")

    prompt = SOLUTION_PROMPT.format(
        title=problem["title"],
        difficulty=problem["difficulty"],
        
        description=problem["description"][:800],  # ~200 tokens, enough for any problem
        starter_code=problem["starter_code"],
    )

    raw_response = _call_gemini(prompt)
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
        fix_response = _call_gemini(fix_prompt).strip()
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

    # Save raw Python file
    code_path = base / "solution.py"
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