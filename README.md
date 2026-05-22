# LeetCode Daily YouTube Bot

An end-to-end automated pipeline that fetches the LeetCode Problem of the Day, generates a correct solution using AI, produces a narrated teaching video with subtitles, and uploads it to YouTube — every single day, with zero manual intervention.

---

## What It Does

Every day at 07:00 IST, the bot:

1. Fetches the LeetCode Problem of the Day via GraphQL
2. Generates a correct C++ solution using Groq's Llama 3.3 70B model
3. Validates the solution by syntax-checking and testing it locally
4. Writes a structured YouTube teaching script using Groq's Llama 3.3 70B model
5. Converts the script to natural-sounding speech using Google Text-to-Speech (gTTS)
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
| **AI — Solution** | Groq Llama 3.3 70B | Fast, accurate C++ code generation with large context window |
| **AI — Script** | Groq Llama 3.3 70B | Produces structured, beginner-friendly teaching scripts |
| **Text-to-Speech** | Google Text-to-Speech (gTTS) | Free, reliable, natural-sounding speech synthesis |
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
├── dashboard.html                 # Single-page dashboard UI (open in browser)
├── serve_dashboard.py             # Simple HTTP server to serve the dashboard
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
  solution_agent.py      -->  Generate C++ solution via Groq Llama 3.3 70B
                         -->  Extract code block (regex)
                         -->  Compile check (C++ syntax validation)
                         -->  Run smoke test (subprocess)
                         -->  output/solution.json
        |
        v
  script_agent.py        -->  Generate teaching script via Groq Llama 3.3 70B
                         -->  Convert to audio via gTTS
                         -->  output/script.txt
                         -->  output/audio/narration.mp3
        |
        v
  code_image.py          -->  Title slide, problem slide, C++ code slide,
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
- Groq API key — free at [console.groq.com](https://console.groq.com)
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

### 4. Get a Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Navigate to **API Keys**
4. Click **Create API Key** and copy it

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
GROQ_API_KEY=your_groq_api_key_here
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

## Dashboard

A beautiful single-page web application is included to visualize the bot's status and latest uploads.

### Viewing the Dashboard

#### Option 1: Using the HTTP Server (Recommended)

```bash
python serve_dashboard.py
```

This will:
- Start a local HTTP server on `http://localhost:8000`
- Automatically open the dashboard in your default browser
- Serve the dashboard with proper file access permissions

Press `CTRL+C` to stop the server.

#### Option 2: Direct File Access

Simply open `dashboard.html` directly in your browser (some features may be limited due to browser security).

### Dashboard Features

The dashboard has 4 main sections:

1. **Overview** — Learn about the bot, workflow, and why automation matters
2. **Status & Dashboard** — Real-time pipeline status with problem details
3. **Latest Video** — Latest uploaded YouTube video with direct link
4. **Technology Stack** — All technologies used and how to get started

### Auto-Refresh

- Dashboard automatically refreshes every 30 seconds
- Manual refresh button available in the top-right
- Shows latest problem, video status, and pipeline completion

### Integration with Pipeline

The dashboard reads data from:
- `output/problem.json` — Current problem details
- `output/upload_record.json` — Latest video info
- `output/pipeline_state.json` — Completion status of each step

After each pipeline run, these files are updated and the dashboard instantly reflects the new status.

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

## Customisation

| What | Where |
|---|---|
| TTS system | Currently uses gTTS in `agents/script_agent.py` |
| Video resolution | `VIDEO_W` and `VIDEO_H` in `video/video_builder.py` |
| Slide colour scheme | Constants at top of `video/code_image.py` |
| Syntax highlight theme | `PYGMENTS_STYLE` in `video/code_image.py` |
| Cron run time | `cron:` in `.github/workflows/daily_bot.yml` |
| LLM model | Model name in `_call_groq()` in `solution_agent.py` and `script_agent.py` (currently Groq llama-3.3-70b-versatile) |

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

**`429 RESOURCE_EXHAUSTED` from Groq**
Your free tier rate limit has been exceeded. Wait a moment and retry. Groq's free tier is generous with 10k requests/day. If you hit limits frequently, consider enabling a paid plan at [console.groq.com](https://console.groq.com).

**`404 NOT_FOUND` for a Groq model**
The model name is not supported. The default is `llama-3.3-70b-versatile`. You can change it in both `solution_agent.py` and `script_agent.py` in the `_call_groq()` function.

**`UnicodeEncodeError` on Windows**
Ensure all `write_text()` calls in `pipeline.py` include `encoding="utf-8"`.

**`FileNotFoundError` for `output\pipeline_result.json`**
The `output` folder does not exist. Run `mkdir output` once before the first pipeline run.

**YouTube browser does not open in CI**
You must generate `youtube_token.json` locally first, then add its contents as the `YOUTUBE_TOKEN_JSON` GitHub Secret.

---