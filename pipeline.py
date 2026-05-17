"""
pipeline.py
───────────
STEP 27: Main orchestration pipeline — runs all steps end-to-end.
STEP 30: Every step is wrapped with retry logic and detailed error handling.

Usage:
  python pipeline.py                     # run full pipeline
  python pipeline.py --skip-upload       # skip YouTube upload
  python pipeline.py --dry-run           # only fetch + solve, no video/upload
  python pipeline.py --date 2024-03-15   # reprocess a specific date (needs cached data)
"""

import argparse
import json
import logging
import os
import sys
import time
import traceback
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from agents.script_agent import generate_script, save_script, generate_audio
from agents.fetch_potd import fetch_potd, save_problem
from agents.solution_agent import generate_solution, save_solution
from video.code_image import generate_all_slides
from video.video_builder import build_video, generate_srt_with_whisper
from agents.youtube_uploader import upload_to_youtube
from agents.telegram_notifier import notify_success, notify_failure

load_dotenv()

# ── Logging setup ──────────────────────────────────────────────────────────────
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"pipeline_{date.today().isoformat()}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s │ %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(log_file), encoding="utf-8"),
    ],
)
log = logging.getLogger("pipeline")


# ── Step wrappers ──────────────────────────────────────────────────────────────

def step(name: str):
    """Decorator: log, time, and handle errors for each pipeline step."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            log.info(f"{'─'*60}")
            log.info(f"▶  {name}")
            log.info(f"{'─'*60}")
            t0 = time.time()
            try:
                result = fn(*args, **kwargs)
                elapsed = time.time() - t0
                log.info(f"✓  {name} completed in {elapsed:.1f}s")
                return result
            except Exception as e:
                elapsed = time.time() - t0
                log.error(f"✗  {name} FAILED after {elapsed:.1f}s: {e}")
                log.debug(traceback.format_exc())
                raise
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator


# ── Individual steps ───────────────────────────────────────────────────────────

@step("STEP 1-7: Fetch LeetCode POTD")
@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=3, max=30),
    retry=retry_if_exception_type((Exception,)),
    reraise=True,
)
def run_fetch(out_dir: str) -> dict:
    sys.path.insert(0, str(Path(__file__).parent / "agents"))
    problem = fetch_potd()
    save_problem(problem, out_dir)
    return problem


@step("STEP 9-14: Generate Solution + Test")
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    reraise=True,
)
def run_solution(problem: dict, out_dir: str) -> dict:
    sys.path.insert(0, str(Path(__file__).parent / "agents"))
    solution = generate_solution(problem)
    save_solution(solution, problem, out_dir)
    return solution


@step("STEP 15-17: Generate Script + Audio")
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    reraise=True,
)
def run_script(problem: dict, solution: dict, out_dir: str) -> tuple[dict, dict]:
    sys.path.insert(0, str(Path(__file__).parent / "agents"))
    script = generate_script(problem, solution)
    save_script(script, problem, out_dir)

    # Check if audio already exists before regenerating
    audio_path = Path(out_dir) / "audio" / "narration.mp3"
    if audio_path.exists():
        log.info("⏭  Skipping audio (already exists)")
        audio_info = {
            "full_audio": str(audio_path),
            "section_audio": {},
            "voice": os.getenv("TTS_VOICE", "en-US-AriaNeural"),
        }
    else:
        audio_info = generate_audio(script, out_dir)

    return script, audio_info


@step("STEP 18-19: Generate Code Images")
def run_images(problem: dict, solution: dict, out_dir: str) -> list[str]:
    sys.path.insert(0, str(Path(__file__).parent / "video"))
    return generate_all_slides(problem, solution, out_dir)


@step("STEP 20-23: Build Video + Subtitles")
def run_video(
    slides: list[str],
    audio_path: str,
    script_text: str,
    out_dir: str,
    date_str: str,
) -> str:
    sys.path.insert(0, str(Path(__file__).parent / "video"))

    srt_path = generate_srt_with_whisper(audio_path, out_dir)
    return build_video(
        slides,
        audio_path,
        script_text=script_text,
        srt_path=srt_path,
        out_dir=out_dir,
        date_str=date_str,
    )


@step("STEP 25-26: Upload to YouTube")
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=5, min=10, max=120),
    reraise=True,
)
def run_upload(video_path: str, problem: dict, solution: dict, script: dict) -> dict:
    sys.path.insert(0, str(Path(__file__).parent / "agents"))
    thumbnail = str(Path("output/images/00_title.png"))
    return upload_to_youtube(video_path, problem, solution, script, thumbnail)


# ── Pipeline state management ──────────────────────────────────────────────────

def load_state(out_dir: str) -> dict:
    state_path = Path(out_dir) / "pipeline_state.json"
    if state_path.exists():
        return json.loads(state_path.read_text())
    return {}


def save_state(state: dict, out_dir: str):
    state_path = Path(out_dir) / "pipeline_state.json"
    state_path.write_text(json.dumps(state, indent=2))


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run_pipeline(
    skip_upload: bool = False,
    dry_run: bool = False,
    date_str: str | None = None,
) -> dict:
    date_str = date_str or date.today().isoformat()
    out_dir = f"output"   # can be parameterized per-date if needed

    log.info(f"{'═'*60}")
    log.info(f"  LeetCode YouTube Bot — {date_str}")
    log.info(f"{'═'*60}")

    state = load_state(out_dir)

    state_path = Path(out_dir) / "pipeline_state.json"
    if state:
        cached_date = state.get("problem", {}).get("date")
        if cached_date and cached_date != date_str:
            state_path.unlink(missing_ok=True)
            log.info(f"Cleared stale cache from {cached_date}")
            state = {}  # reset to empty after clearing

    results = {"date": date_str, "steps": {}}
    t_start = time.time()

    try:
        # ── STEP 1-7: Fetch POTD ────────────────────────────────────────────
        if "problem" not in state:
            problem = run_fetch(out_dir)
            state["problem"] = problem
            save_state(state, out_dir)
        else:
            log.info("⏭  Skipping fetch (cached)")
            problem = state["problem"]

        results["steps"]["fetch"] = "✓"
        results["problem_title"] = problem["title"]

        # ── STEP 9-14: Solution ─────────────────────────────────────────────
        if "solution" not in state:
            solution = run_solution(problem, out_dir)
            state["solution"] = solution
            save_state(state, out_dir)
        else:
            log.info("⏭  Skipping solution (cached)")
            solution = state["solution"]

        results["steps"]["solution"] = "✓"

        if dry_run:
            log.info("Dry-run mode: stopping after solution generation.")
            return results

        # ── STEP 15-17: Script + Audio ──────────────────────────────────────
        if "script" not in state:
            script, audio_info = run_script(problem, solution, out_dir)
            state["script"]     = script
            state["audio_info"] = audio_info
            save_state(state, out_dir)  # saves immediately after both are done
        else:
            # Restore from cache but verify audio file exists
            script     = state["script"]
            audio_info = state.get("audio_info", {})
            audio_path = Path(out_dir) / "audio" / "narration.mp3"
            if not audio_path.exists():
                log.info("Script cached but audio missing — regenerating audio only …")
                sys.path.insert(0, str(Path(__file__).parent / "agents"))
                audio_info = generate_audio(script, out_dir)
                state["audio_info"] = audio_info
                save_state(state, out_dir)
            else:
                log.info("⏭  Skipping script/audio (cached)")


        results["steps"]["script_audio"] = "✓"

        # ── STEP 18-19: Images ──────────────────────────────────────────────
        if "slides" not in state:
            slides = run_images(problem, solution, out_dir)
            state["slides"] = slides
            save_state(state, out_dir)
        else:
            log.info("⏭  Skipping images (cached)")
            slides = state["slides"]

        results["steps"]["images"] = f"✓ ({len(slides)} slides)"

        # ── STEP 20-23: Video ───────────────────────────────────────────────────────
        cached_video = state.get("video_path")
        if cached_video and Path(cached_video).exists():
            log.info(f"⏭  Skipping video (cached) → {cached_video}")
            video_path = cached_video
        else:
            video_path = run_video(
                slides,
                audio_info["full_audio"],
                script.get("clean_script", ""),
                out_dir,
                date_str,
            )
            state["video_path"] = video_path
            save_state(state, out_dir)

        results["steps"]["video"] = "✓"
        results["video_path"] = video_path

        # ── STEP 25-26: Upload ──────────────────────────────────────────────
        if skip_upload:
            log.info("⏭  Skipping YouTube upload (--skip-upload)")
            results["steps"]["upload"] = "skipped"
        elif "upload" not in state:
            upload_result = run_upload(video_path, problem, solution, script)
            state["upload"] = upload_result
            save_state(state, out_dir)
            results["steps"]["upload"] = "✓"
            results["youtube_url"] = upload_result["url"]
        else:
            log.info("⏭  Skipping upload (cached)")
            results["steps"]["upload"] = "✓ (cached)"
            results["youtube_url"] = state["upload"].get("url", "")

    except Exception as e:
        results["error"] = str(e)
        results["traceback"] = traceback.format_exc()
        log.error(f"Pipeline failed: {e}")
        raise

    finally:
        elapsed = time.time() - t_start
        results["duration_seconds"] = round(elapsed, 1)
        summary_path = Path(out_dir) / "pipeline_result.json"
        summary_path.write_text(json.dumps(results, indent=2, ensure_ascii=True), encoding="utf-8")
        log.info(f"\nPipeline result → {summary_path}")
        log.info(f"Total time: {elapsed:.1f}s")

        # Send Telegram notification
        if "error" in results:
            notify_failure(results)
        else:
            notify_success(results)

    log.info(f"\n{'═'*60}")
    log.info(f"  [OK] Pipeline complete!")
    log.info(f"  [VIDEO]  : {results.get('video_path', 'N/A')}")
    log.info(f"  [YOUTUBE]: {results.get('youtube_url', 'N/A')}")
    log.info(f"{'═'*60}")

    return results


# ── CLI ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LeetCode Daily YouTube Bot")
    parser.add_argument("--skip-upload", action="store_true", help="Skip YouTube upload")
    parser.add_argument("--dry-run",     action="store_true", help="Fetch + solve only")
    parser.add_argument("--date",        type=str,            help="Override date (YYYY-MM-DD)")
    parser.add_argument("--clear-cache", action="store_true", help="Clear pipeline state cache")
    args = parser.parse_args()

    if args.clear_cache:
        cache = Path("output/pipeline_state.json")
        if cache.exists():
            cache.unlink()
            print("Cache cleared.")

    run_pipeline(
        skip_upload=args.skip_upload,
        dry_run=args.dry_run,
        date_str=args.date,
    )