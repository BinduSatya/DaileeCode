"""
telegram_notifier.py
────────────────────
Sends a daily pipeline status summary to a Telegram bot.
"""

import os
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")


def send_message(text: str) -> bool:
    """Send a plain text message to the Telegram bot."""
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram not configured — skipping notification")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"Telegram notification failed: {e}")
        return False


def notify_success(results: dict) -> None:
    steps = results.get("steps", {})
    step_lines = "\n".join(
        f"  {'OK' if v == 'skipped' or 'skipped' not in str(v) else 'SKIP'} {k} — {v}"
        for k, v in steps.items()
    )

    msg = f"""
<b>LeetCode YouTube Bot — Daily Report</b>
<b>Date:</b> {results.get('date', date.today())}
<b>Problem:</b> {results.get('problem_title', 'N/A')}

<b>Steps:</b>
{step_lines}

<b>Duration:</b> {results.get('duration_seconds', '?')}s
<b>YouTube:</b> {results.get('youtube_url', 'Not uploaded')}

Status: SUCCESS
""".strip()

    send_message(msg)


def notify_failure(results: dict) -> None:
    error = results.get("error", "Unknown error")

    # Only show the first 2 lines of the error — keep it clean
    short_error = "\n".join(error.splitlines()[:2])

    msg = f"""
<b>LeetCode YouTube Bot — FAILED</b>
<b>Date:</b> {results.get('date', date.today())}
<b>Problem:</b> {results.get('problem_title', 'N/A')}

<b>Failed at:</b> {_last_completed_step(results)}
<b>Error:</b> <code>{short_error}</code>

<b>Duration:</b> {results.get('duration_seconds', '?')}s
""".strip()

    send_message(msg)


def _last_completed_step(results: dict) -> str:
    steps = results.get("steps", {})
    if not steps:
        return "startup"
    return list(steps.keys())[-1]