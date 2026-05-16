# LeetCode Daily YouTube Bot

An end-to-end automated pipeline that fetches the LeetCode Problem of the Day, generates a correct solution using AI, produces a narrated teaching video with subtitles, and uploads it to YouTube — every single day, with zero manual intervention.

---

## What It Does

Every day at 08:00 UTC, the bot:

1. Fetches the LeetCode Problem of the Day via GraphQL
2. Generates a correct Python solution using Google Gemini AI
3. Validates the solution by compiling and running it locally
4. Writes a structured YouTube teaching script using Gemini
5. Converts the script to natural-sounding speech using Microsoft Edge TTS
6. Renders syntax-highlighted code slides using Pygments and Pillow
7. Assembles everything into a 1080p MP4 video using MoviePy
8. Adds auto-generated subtitles
9. Uploads the final video to YouTube with SEO-optimised title, description, and tags

---

## Problem Statement

Creating daily educational coding content is extremely time-consuming. A creator would need to: read the problem, think through a solution, write and test code, record audio narration, design visuals, edit a video, and upload it with proper metadata — every single day. This bot automates the entire workflow end-to-end so a YouTube channel can publish consistent, high-quality LeetCode content with no daily effort.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **AI — Solution** | Google Gemini 2.0 Flash | Fast, accurate code generation with large context window |
| **AI — Script** | Google Gemini 2.0 Flash | Produces structured, beginner-friendly teaching scripts |
| **Text-to-Speech** | Microsoft Edge TTS | Free, no API key needed, natural-sounding voices |
| **Code Highlighting** | Pygments + Pillow | Industry-standard syntax highlighter; Pillow for compositing |
| **Video Assembly** | MoviePy | Pure Python video editing, no external editor needed |
| **Subtitles** | OpenAI Whisper | Word-level transcription directly from the generated audio |
| **YouTube Upload** | YouTube Data API v3 | Official Google API, supports resumable uploads |
| **Data Fetching** | LeetCode GraphQL API | Provides structured problem data including code snippets |
| **Retry Logic** | Tenacity | Declarative retry policies with exponential backoff |
| **Automation** | GitHub Actions + Cron | Free CI/CD runner with scheduled daily execution |
| **Config** | python-dotenv | Clean separation of secrets from code |

---

## Project Structure

```
leetcode-youtube-bot/
│
├── agents/                        # Core pipeline agents
│   ├── fetch_potd.py              # Fetches POTD via LeetCode GraphQL API
│   ├── solution_agent.py          # Generates, extracts, compiles & tests solution
│   ├── script_agent.py            # Generates teaching script and TTS audio
│   └── youtube_uploader.py        # Handles OAuth2 and YouTube upload
│
├── video/                         # Video generation modules
│   ├── code_image.py              # Builds syntax-highlighted slide images
│   └── video_builder.py           # Assembles slides + audio into final MP4
│
├── .github/
│   └── workflows/
│       └── daily_bot.yml          # GitHub Actions cron workflow
│
├── output/                        # Auto-created on first run
│   ├── audio/                     # narration.mp3 and per-section audio files
│   ├── images/                    # Slide PNGs (title, problem, code, complexity, outro)
│   ├── videos/                    # final_YYYY-MM-DD.mp4
│   └── subtitles/                 # narration.srt (if Whisper is installed)
│
├── logs/                          # Daily timestamped log files
├── pipeline.py                    # Main orchestrator with caching and retries
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## How It Works

```
LeetCode GraphQL API
        |
        v
  fetch_potd.py          -->  output/problem.json
        |
        v
  solution_agent.py      -->  Generate solution via Gemini
                         -->  Extract code block (regex)
                         -->  Compile check (Python ast)
                         -->  Run smoke test (subprocess)
                         -->  output/solution.json
        |
        v
  script_agent.py        -->  Generate teaching script via Gemini
                         -->  Convert to audio via Edge TTS
                         -->  output/script.txt
                         -->  output/audio/narration.mp3
        |
        v
  code_image.py          -->  Title slide, problem slide, code slide,
                              complexity slide, outro slide
                         -->  output/images/*.png
        |
        v
  video_builder.py       -->  Assemble slides + audio via MoviePy
                         -->  Generate subtitles via Whisper
                         -->  output/videos/final_YYYY-MM-DD.mp4
        |
        v
  youtube_uploader.py    -->  OAuth2 authentication
                         -->  Upload with metadata and thumbnail
                         -->  Returns YouTube URL
```

Each step saves its output to disk and records its completion in `output/pipeline_state.json`. If the pipeline crashes at any step, re-running it resumes from where it left off. The cache is automatically cleared when the date changes so each new day starts fresh.

---

## Prerequisites

**Python version:** 3.11 or higher

**System tools required:**

FFmpeg (video encoding):
```bash
# Windows
choco install ffmpeg

# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg
```

ImageMagick (text rendering for subtitles):
```bash
# Windows — download from https://imagemagick.org/script/download.php

# macOS
brew install imagemagick

# Ubuntu / Debian
sudo apt install imagemagick
```

**API access required:**
- Google Gemini API key — free at [aistudio.google.com](https://aistudio.google.com)
- Google Cloud project with YouTube Data API v3 enabled
- OAuth 2.0 client credentials JSON from Google Cloud Console

---

## Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/leetcode-youtube-bot.git
cd leetcode-youtube-bot
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install --upgrade pip setuptools
pip install -r requirements.txt
```

> `openai-whisper` is optional. If it fails to install, the pipeline automatically
> falls back to sentence-split subtitles. Skip it with no impact on the rest of the pipeline.

### 4. Get a Gemini API key

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click **Get API key** → **Create API key**
3. Copy the key

### 5. Set up YouTube API credentials

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project
3. Navigate to **APIs & Services** → **Enable APIs** → search **YouTube Data API v3** → Enable
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Desktop App** → Create
6. Click **Download JSON** → rename the file to `client_secrets.json`
7. Place `client_secrets.json` in the project root

### 6. Configure environment variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` with your values:

```env
GEMINI_API_KEY=your_gemini_api_key_here
YOUTUBE_CLIENT_SECRETS=client_secrets.json
YOUTUBE_TOKEN_FILE=youtube_token.json
YOUTUBE_PRIVACY=public
TTS_VOICE=en-US-AriaNeural
```

### 7. Create the output directory

```bash
mkdir output
```

---

## Running the Pipeline

### Full run (recommended for first time)

```bash
python pipeline.py
```

On the first run, a browser window opens asking you to sign in to Google and grant YouTube upload permission. After approval, the token is saved to `youtube_token.json` and all future runs are fully silent.

### Test without uploading to YouTube

```bash
python pipeline.py --skip-upload
```

### Fetch and solve only, no video or upload

```bash
python pipeline.py --dry-run
```

### Clear cache and re-run everything from scratch

```bash
python pipeline.py --clear-cache
```

### Run individual steps for debugging

```bash
python agents/fetch_potd.py        # Fetch today's problem only
python agents/solution_agent.py    # Generate and test solution only
python agents/script_agent.py      # Generate script and audio only
python video/code_image.py         # Generate slide images only
python video/video_builder.py      # Assemble video only
python agents/youtube_uploader.py  # Upload to YouTube only
```

---

## Daily Automation via GitHub Actions

### Step 1 — Run locally first

Run the full pipeline locally at least once so that `youtube_token.json` is generated. GitHub Actions needs this token to upload without a browser.

### Step 2 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/leetcode-youtube-bot.git
git push -u origin main
```

### Step 3 — Add GitHub Secrets

Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret | Value |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key |
| `YOUTUBE_CLIENT_SECRETS_JSON` | Paste the full contents of `client_secrets.json` |
| `YOUTUBE_TOKEN_JSON` | Paste the full contents of `youtube_token.json` |
| `PAT_TOKEN` | GitHub Personal Access Token with `secrets:write` scope |

### Step 4 — Add GitHub Variables (optional)

Go to **Settings** → **Secrets and variables** → **Actions** → **Variables** tab:

| Variable | Default |
|---|---|
| `YOUTUBE_PRIVACY` | `public` |
| `TTS_VOICE` | `en-US-AriaNeural` |

The workflow runs automatically at **08:00 UTC every day**. You can also trigger it manually from the **Actions** tab → select the workflow → **Run workflow**.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Gemini API key from Google AI Studio |
| `YOUTUBE_CLIENT_SECRETS` | Yes | — | Path to OAuth client secrets JSON |
| `YOUTUBE_TOKEN_FILE` | No | `youtube_token.json` | Where to cache the OAuth token |
| `YOUTUBE_PRIVACY` | No | `public` | Video visibility: `public`, `unlisted`, or `private` |
| `TTS_VOICE` | No | `en-US-AriaNeural` | Edge TTS voice name |

List all available TTS voices:
```bash
edge-tts --list-voices
```

---

## Customisation

| What | Where |
|---|---|
| TTS voice | `TTS_VOICE` in `.env` |
| Video resolution | `VIDEO_W` and `VIDEO_H` in `video/video_builder.py` |
| Slide colour scheme | Constants at top of `video/code_image.py` |
| Syntax highlight theme | `PYGMENTS_STYLE` in `video/code_image.py` |
| Cron run time | `cron:` in `.github/workflows/daily_bot.yml` |
| Gemini model | `GEMINI_MODEL` in `solution_agent.py` and `script_agent.py` |

---

## Error Handling

Every step uses `tenacity` for automatic retries with exponential backoff:

| Step | Attempts | Backoff range |
|---|---|---|
| Fetch POTD | 4 | 3 – 30 seconds |
| Generate solution | 3 | 5 – 60 seconds |
| Generate script and audio | 3 | 5 – 60 seconds |
| YouTube upload | 3 | 10 – 120 seconds |

---

## Common Issues

**`No module named 'requests'` or similar**
You have not installed dependencies into your virtual environment. Run `pip install -r requirements.txt` with the venv activated.

**`429 RESOURCE_EXHAUSTED` from Gemini**
Your free tier daily quota is exhausted. Wait until midnight US Pacific Time for it to reset, or enable billing at [console.cloud.google.com/billing](https://console.cloud.google.com/billing). The pipeline makes only 2 Gemini calls per day under normal use.

**`404 NOT_FOUND` for a Gemini model**
The model name is not supported by the installed SDK version. Change `GEMINI_MODEL` in both agent files to `gemini-2.0-flash-lite`.

**`UnicodeEncodeError` on Windows**
Ensure all `write_text()` calls in `pipeline.py` include `encoding="utf-8"`.

**`FileNotFoundError` for `output\pipeline_result.json`**
The `output` folder does not exist. Run `mkdir output` once before the first pipeline run.

**YouTube browser does not open in CI**
You must generate `youtube_token.json` locally first, then add its contents as the `YOUTUBE_TOKEN_JSON` GitHub Secret.

---

## Gemini Free Tier Limits

| Model | Requests / minute | Requests / day |
|---|---|---|
| `gemini-2.0-flash` | 15 | 1,500 |
| `gemini-2.0-flash-lite` | 30 | 1,500 |
| `gemini-2.5-flash-preview-05-20` | 10 | 500 |

This bot makes 2 Gemini API calls per daily run, well within all limits.

---

## License

MIT — free to use, modify, and distribute.