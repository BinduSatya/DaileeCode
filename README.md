# 🎬 LeetCode Daily YouTube Bot

Fully automated pipeline that **fetches** the LeetCode Problem of the Day, **solves it** with Gemini AI, **generates a teaching video**, and **uploads it to YouTube** — every single day.

```
LeetCode POTD → Gemini Solution → Teaching Script → Edge-TTS Audio
→ Pygments Code Images → MoviePy Video → Whisper Subtitles → YouTube Upload
```

---

## 📁 Project Structure

```
leetcode-youtube-bot/
├── agents/
│   ├── fetch_potd.py          # STEP 5-7:  LeetCode GraphQL → problem.json
│   ├── solution_agent.py      # STEP 9-14: Gemini solution + compile + test
│   ├── script_agent.py        # STEP 15-17: Teaching script + Edge-TTS audio
│   └── youtube_uploader.py    # STEP 25-26: OAuth2 YouTube Data API upload
├── video/
│   ├── code_image.py          # STEP 18-19: Pygments + Pillow slide images
│   └── video_builder.py       # STEP 20-23: MoviePy video + Whisper subtitles
├── .github/workflows/
│   └── daily_bot.yml          # STEP 28-29: GitHub Actions + cron schedule
├── output/                    # Auto-created — all generated artefacts
│   ├── audio/                 #   narration.mp3 + per-section audio
│   ├── images/                #   00_title.png … 04_outro.png
│   ├── videos/                #   final_YYYY-MM-DD.mp4
│   └── subtitles/             #   narration.srt (if Whisper installed)
├── logs/                      # Daily log files
├── pipeline.py                # STEP 27-30: Full orchestration + retries
├── requirements.txt
└── .env.example
```

---

## 🚀 Quick Start

### 1. Clone & create virtual environment

```bash
git clone https://github.com/your-username/leetcode-youtube-bot.git
cd leetcode-youtube-bot
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get a Gemini API key (STEP 8)

1. Go to [aistudio.google.com](https://aistudio.google.com) → **Get API key**
2. Copy the key

### 3. Set up YouTube API (STEP 25)

1. Open [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project → **Enable APIs** → search "YouTube Data API v3" → Enable
3. **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID** → Desktop App
4. Download → rename to `client_secrets.json` → place in project root

### 4. Configure `.env`

```bash
cp .env.example .env
# Edit .env:
GEMINI_API_KEY=your_key_here
YOUTUBE_CLIENT_SECRETS=client_secrets.json
YOUTUBE_PRIVACY=public          # or unlisted for testing
```

### 5. Run the pipeline

```bash
# Full run (will open browser for YouTube OAuth on first run)
python pipeline.py

# Test without uploading
python pipeline.py --skip-upload

# Fetch + solve only (no video, no upload)
python pipeline.py --dry-run

# Clear cache and re-run from scratch
python pipeline.py --clear-cache
```

---

## ⚙️ Individual Steps

You can run each step independently for development/debugging:

```bash
# STEP 5-7: Fetch today's POTD
python agents/fetch_potd.py

# STEP 9-14: Generate + test solution
python agents/solution_agent.py

# STEP 15-17: Generate script + audio
python agents/script_agent.py

# STEP 18-19: Generate slide images
python video/code_image.py

# STEP 20-23: Build video
python video/video_builder.py

# STEP 25-26: Upload to YouTube
python agents/youtube_uploader.py
```

---

## 🤖 Daily Automation via GitHub Actions (STEP 28-29)

### Set up GitHub Secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret name                  | Value |
|------------------------------|-------|
| `GEMINI_API_KEY`             | Your Gemini API key |
| `YOUTUBE_CLIENT_SECRETS_JSON`| Full contents of `client_secrets.json` |
| `YOUTUBE_TOKEN_JSON`         | Full contents of `youtube_token.json` (run locally first to generate) |
| `PAT_TOKEN`                  | GitHub Personal Access Token with `secrets:write` scope (for token refresh) |

### Set up GitHub Variables (optional)

| Variable name    | Default value        |
|------------------|----------------------|
| `YOUTUBE_PRIVACY`| `public`             |
| `TTS_VOICE`      | `en-US-AriaNeural`   |

### Schedule

The workflow runs at **08:00 UTC daily** (`cron: "0 8 * * *"`).
You can also trigger it manually from the **Actions** tab → **Run workflow**.

---

## 🛠️ Pipeline Steps Reference

| # | Step | File | Technology |
|---|------|------|------------|
| 5-7 | Fetch POTD | `agents/fetch_potd.py` | LeetCode GraphQL API |
| 8 | Gemini key | `.env` | Google AI Studio |
| 9-11 | Generate solution | `agents/solution_agent.py` | Gemini 1.5 Flash |
| 12 | Extract code | `solution_agent.py` | regex |
| 13 | Compile check | `solution_agent.py` | Python `ast` |
| 14 | Run test cases | `solution_agent.py` | subprocess |
| 15 | Teaching script | `agents/script_agent.py` | Gemini 1.5 Flash |
| 16-17 | TTS audio | `agents/script_agent.py` | Microsoft Edge TTS |
| 18-19 | Code images | `video/code_image.py` | Pygments + Pillow |
| 20-22 | Build video | `video/video_builder.py` | MoviePy |
| 23 | Subtitles | `video/video_builder.py` | OpenAI Whisper |
| 25-26 | YouTube upload | `agents/youtube_uploader.py` | YouTube Data API v3 |
| 27 | Orchestration | `pipeline.py` | — |
| 28 | GitHub Actions | `.github/workflows/daily_bot.yml` | GitHub Actions |
| 29 | Cron schedule | `.github/workflows/daily_bot.yml` | cron `0 8 * * *` |
| 30 | Retry logic | All agents | tenacity |

---

## 🔧 Error Handling (STEP 30)

Every step uses `tenacity` for automatic retries:

- **Fetch POTD** — 4 attempts, exponential backoff (3–30 s)
- **Solution generation** — 3 attempts, 5–60 s backoff
- **Script/audio** — 3 attempts, 5–60 s backoff
- **YouTube upload** — 3 attempts, 10–120 s backoff (handles rate limits)

The pipeline also caches each completed step in `output/pipeline_state.json`, so if it crashes mid-run, it resumes where it left off (rather than regenerating everything).

---

## 🎨 Customisation

| What | Where |
|------|-------|
| Change TTS voice | `TTS_VOICE` in `.env` (see `edge-tts --list-voices`) |
| Change video resolution | `VIDEO_W/H` in `video_builder.py` |
| Change slide colors | Constants at top of `video/code_image.py` |
| Change code style | `PYGMENTS_STYLE` in `video/code_image.py` |
| Adjust cron time | `cron:` in `.github/workflows/daily_bot.yml` |
| Upload privacy | `YOUTUBE_PRIVACY` in `.env` |

---

## 📝 Notes

- **Whisper** (`openai-whisper`) requires ~2 GB of VRAM and is skipped in CI if not available. The pipeline falls back to sentence-split subtitles automatically.
- **YouTube OAuth token** must be generated locally on first run (opens browser). After that, the token is cached and refreshed automatically.
- The pipeline is idempotent: re-running it on the same day will skip already-completed steps unless you pass `--clear-cache`.
