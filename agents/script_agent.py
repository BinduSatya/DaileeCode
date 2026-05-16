"""
script_agent.py
───────────────
STEP 15: Generate a YouTube-ready teaching script from the solution.
STEP 16-17: Convert that script to audio using Microsoft Edge TTS (free, no API key).

Audio file → output/audio/narration.mp3
Script file → output/script.txt
"""

import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path

import edge_tts
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")
log = logging.getLogger(__name__)

_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy"))
GEMINI_MODEL = "gemini-2.0-flash-lite"

DEFAULT_VOICE = os.getenv("TTS_VOICE", "en-US-AriaNeural")

# ── STEP 15: Script generation ─────────────────────────────────────────────────
SCRIPT_PROMPT = """\
You are a YouTube coding educator with an engaging, friendly teaching style.

Write a narration script for a short YouTube video (3–5 minutes) explaining the following
LeetCode problem and solution.

## Problem
Title: {title}
Difficulty: {difficulty}
URL: {url}

## Solution Code
```python
{code}
```

## Explanation Notes
{explanation}

## Script Rules
- Write in a conversational, energetic tone (like a knowledgeable friend, not a textbook).
- Structure the script in these LABELED sections (use these exact labels on their own line):
  [INTRO]
  [PROBLEM BREAKDOWN]
  [INTUITION]
  [WALKTHROUGH]
  [CODE EXPLANATION]
  [COMPLEXITY]
  [OUTRO]
- Each section should flow naturally into the next.
- Do NOT include stage directions, [pause], or sound effects.
- Write ONLY spoken words — no markdown, no asterisks, no bullet symbols.
- End with a call to action to like, subscribe, and comment.
- Target length: ~450–550 words (reads as ~3–4 minutes at normal pace).
"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def generate_script(problem: dict, solution: dict) -> dict:
    """Generate a structured YouTube script using Gemini."""
    log.info("Generating teaching script …")

    prompt = SCRIPT_PROMPT.format(
        title=problem["title"],
        difficulty=problem["difficulty"],
        url=problem["url"],
        code=solution["code"][:2000],
        explanation=solution["explanation"][:1500],
    )

    response = _client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=3000),
    )
    script_text = response.text.strip()

    # Parse sections
    section_labels = [
        "INTRO", "PROBLEM BREAKDOWN", "INTUITION",
        "WALKTHROUGH", "CODE EXPLANATION", "COMPLEXITY", "OUTRO"
    ]
    sections = {}
    remaining = script_text

    for i, label in enumerate(section_labels):
        pattern = rf"\[{label}\]([\s\S]*?)(?=\[{'|'.join(section_labels[i+1:])}|\Z)" if i < len(section_labels) - 1 else rf"\[{label}\]([\s\S]*)"
        match = re.search(pattern, remaining)
        if match:
            sections[label] = match.group(1).strip()

    # Full clean script (strip labels for TTS)
    clean_script = re.sub(r"\[[A-Z ]+\]", "", script_text).strip()
    clean_script = re.sub(r"\n{3,}", "\n\n", clean_script)

    log.info(f"✓ Script generated ({len(clean_script.split())} words)")
    return {
        "full_script": script_text,
        "clean_script": clean_script,
        "sections": sections,
        "word_count": len(clean_script.split()),
    }


# ── STEP 16-17: Edge-TTS narration ────────────────────────────────────────────
async def _synthesize(text: str, output_path: Path, voice: str) -> Path:
    """Async Edge-TTS synthesis."""
    communicate = edge_tts.Communicate(text=text, voice=voice)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    await communicate.save(str(output_path))
    return output_path


def generate_audio(
    script: dict,
    out_dir: str = "output",
    voice: str = DEFAULT_VOICE,
) -> dict:
    """
    Convert the clean script to MP3 audio.
    Also generates per-section audio files for video timing.
    """
    base = Path(out_dir) / "audio"
    base.mkdir(parents=True, exist_ok=True)

    # Full narration
    full_path = base / "narration.mp3"
    log.info(f"Synthesizing full narration with voice={voice} …")
    asyncio.run(_synthesize(script["clean_script"], full_path, voice))
    log.info(f"✓ Audio saved → {full_path}")

    # Per-section audio (for scene timing)
    section_paths = {}
    for label, text in script.get("sections", {}).items():
        if not text.strip():
            continue
        safe_label = label.lower().replace(" ", "_")
        section_path = base / f"section_{safe_label}.mp3"
        asyncio.run(_synthesize(text, section_path, voice))
        section_paths[label] = str(section_path)
        log.info(f"  ✓ Section '{label}' → {section_path.name}")

    return {
        "full_audio": str(full_path),
        "section_audio": section_paths,
        "voice": voice,
    }


def save_script(script: dict, problem: dict, out_dir: str = "output") -> Path:
    """Save script text and JSON."""
    base = Path(out_dir)
    base.mkdir(parents=True, exist_ok=True)

    txt_path = base / "script.txt"
    txt_path.write_text(script["full_script"], encoding="utf-8")

    json_path = base / "script.json"
    json_path.write_text(
        json.dumps(
            {
                "problem_title": problem["title"],
                "word_count": script["word_count"],
                "sections": list(script["sections"].keys()),
                "full_script": script["full_script"],
                "clean_script": script["clean_script"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    log.info(f"Saved script → {txt_path}")
    return json_path


# ── CLI test ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    for name, path in [("problem", "output/problem.json"), ("solution", "output/solution.json")]:
        if not Path(path).exists():
            print(f"Missing {path}. Run previous steps first.")
            sys.exit(1)

    problem = json.loads(Path("output/problem.json").read_text())
    solution = json.loads(Path("output/solution.json").read_text())

    script = generate_script(problem, solution)
    save_script(script, problem)

    audio_info = generate_audio(script)
    print(f"\nAudio: {audio_info['full_audio']}")
    print(f"Sections: {list(audio_info['section_audio'].keys())}")
