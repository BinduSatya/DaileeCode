"""
youtube_uploader.py
───────────────────
STEP 25-26: Upload the rendered video to YouTube using the YouTube Data API v3.

Setup (one-time):
  1. Go to console.cloud.google.com → Create Project
  2. Enable "YouTube Data API v3"
  3. Create OAuth 2.0 credentials (Desktop App)
  4. Download client_secrets.json → project root
  5. Set YOUTUBE_CLIENT_SECRETS=client_secrets.json in .env
  6. First run will open browser for OAuth consent; token is cached after that.

Environment variables (from .env):
  YOUTUBE_CLIENT_SECRETS  path to client_secrets.json
  YOUTUBE_TOKEN_FILE      where to cache the OAuth token  (default: youtube_token.json)
  YOUTUBE_PRIVACY         public | unlisted | private     (default: public)
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from logger import log

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

CLIENT_SECRETS = os.getenv("YOUTUBE_CLIENT_SECRETS", "client_secrets.json")
TOKEN_FILE     = os.getenv("YOUTUBE_TOKEN_FILE",      "youtube_token.json")
PRIVACY        = os.getenv("YOUTUBE_PRIVACY",         "public")

CATEGORY_EDUCATION = "27"   # YouTube category ID for Education
MAX_TITLE_LEN = 100
MAX_DESCRIPTION_LEN = 5000


# ── OAuth helper ───────────────────────────────────────────────────────────────

def _get_credentials() -> Credentials:
    creds = None

    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log.info("Refreshing YouTube OAuth token …")
            creds.refresh(Request())
        else:
            if not Path(CLIENT_SECRETS).exists():
                raise FileNotFoundError(
                    f"client_secrets.json not found at '{CLIENT_SECRETS}'.\n"
                    "Download it from Google Cloud Console → APIs & Services → Credentials."
                )
            log.info("Opening browser for YouTube OAuth consent …")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
            creds = flow.run_local_server(port=0)

        Path(TOKEN_FILE).write_text(creds.to_json())
        log.info(f"Token saved → {TOKEN_FILE}")

    return creds


# ── Metadata builders ──────────────────────────────────────────────────────────

def _build_title(problem: dict) -> str:
    title = (
        f"LeetCode Daily {problem['date']} | "
        f"#{problem['id']} {problem['title']} [{problem['difficulty']}] | C++ Solution"
    )
    return title[:MAX_TITLE_LEN]


def _build_description(problem: dict, solution: dict, script: dict) -> str:
    tags_str = " | ".join(problem.get("tags", []))
    desc = f"""\
🔥 LeetCode Problem of the Day — {problem['date']}

📌 Problem: {problem['title']}
🏆 Difficulty: {problem['difficulty']}
🔗 Problem Link: {problem['url']}
🏷️  Topics: {tags_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 In this video:
• Problem walkthrough
• Intuition & approach
• C++ solution with explanation
• Time & Space complexity analysis

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Solution Summary
{solution.get('explanation', '')[:600]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👍 Like • 🔔 Subscribe • 💬 Comment your approach below!

#LeetCode #CodingInterview #Python #DataStructures #Algorithms
#LeetCodeDaily #CompetitiveProgramming #{problem['difficulty']}
"""
    return desc[:MAX_DESCRIPTION_LEN]


def _build_tags(problem: dict) -> list[str]:
    base = [
        "LeetCode", "LeetCode Daily", "Python", "Coding Interview",
        "Data Structures", "Algorithms", "Programming", problem["difficulty"],
        problem["title"], "LeetCode Solution", "Tech Interview", "FAANG",
    ]
    topic_tags = problem.get("tags", [])[:8]
    return list(dict.fromkeys(base + topic_tags))[:30]   # YouTube allows max 30 tags


# ── STEP 26: Upload ────────────────────────────────────────────────────────────

def upload_to_youtube(
    video_path: str,
    problem: dict,
    solution: dict,
    script: dict | None = None,
    thumbnail_path: str | None = None,
) -> dict:
    """
    Upload video to YouTube. Returns dict with videoId and url.
    """
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    script = script or {}
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    title       = _build_title(problem)
    description = _build_description(problem, solution, script)
    tags        = _build_tags(problem)

    log.info(f"Uploading '{title}' …")

    body = {
        "snippet": {
            "title":       title,
            "description": description,
            "tags":        tags,
            "categoryId":  CATEGORY_EDUCATION,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus":           PRIVACY,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 5,  # 5 MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            log.info(f"  Upload progress: {pct}%")

    video_id  = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    log.info(f"✓ Uploaded → {video_url}")

    # Optional: set thumbnail
    if thumbnail_path and Path(thumbnail_path).exists():
        _set_thumbnail(youtube, video_id, thumbnail_path)

    result = {
        "videoId":  video_id,
        "url":      video_url,
        "title":    title,
        "privacy":  PRIVACY,
    }

    # Cache upload record
    record_path = Path("output") / "upload_record.json"
    record_path.write_text(json.dumps(result, indent=2))
    log.info(f"Upload record saved → {record_path}")

    return result


def _set_thumbnail(youtube, video_id: str, thumbnail_path: str):
    """Set custom thumbnail for the video."""
    log.info(f"Setting thumbnail: {thumbnail_path}")
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(thumbnail_path, mimetype="image/png"),
    ).execute()
    log.info("✓ Thumbnail set")


# ── CLI test ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import glob

    videos = sorted(glob.glob("output/videos/final_*.mp4"))
    if not videos:
        print("No video found. Run video_builder.py first.")
        sys.exit(1)

    for path in ["output/problem.json", "output/solution.json"]:
        if not Path(path).exists():
            print(f"Missing {path}")
            sys.exit(1)

    video_path = videos[-1]   # use latest
    problem    = json.loads(Path("output/problem.json").read_text())
    solution   = json.loads(Path("output/solution.json").read_text())
    script     = json.loads(Path("output/script.json").read_text()) if Path("output/script.json").exists() else {}

    # Use title slide as thumbnail
    thumbnail = "output/images/00_title.png"

    result = upload_to_youtube(video_path, problem, solution, script, thumbnail)
    print(json.dumps(result, indent=2))
