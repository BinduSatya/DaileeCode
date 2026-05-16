"""
video_builder.py
────────────────
STEP 20-22: Assemble multiple image slides + narration audio into a final MP4 video.
STEP 23:    Burn auto-generated SRT subtitles onto the video (requires whisper in prod).

Architecture
  - Each slide is displayed for its proportional share of the full narration audio.
  - Smooth crossfade transitions between slides (0.5 s).
  - Subtitle text is overlaid using MoviePy TextClip (no external tool needed for basic subs).
  - If a whisper-generated .srt file is present, it is burned in instead.

Output → output/videos/final_<YYYY-MM-DD>.mp4
"""

import json
import logging
import os
import re
import sys
from datetime import date
from pathlib import Path

from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
)
from moviepy.video.fx.all import fadein, fadeout

logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")
log = logging.getLogger(__name__)

VIDEO_W, VIDEO_H = 1920, 1080
FPS = 24
TRANSITION_DURATION = 0.5   # cross-fade seconds between slides
SUBTITLE_MARGIN = 60        # px from bottom

# ── Timing helpers ─────────────────────────────────────────────────────────────

def _audio_duration(path: str) -> float:
    clip = AudioFileClip(path)
    dur = clip.duration
    clip.close()
    return dur


def _slide_durations(n_slides: int, total_duration: float) -> list[float]:
    """
    Distribute total audio duration across slides.
    Slide 0 (title)   → 8 s
    Slide -1 (outro)  → 10 s
    Remaining         → split evenly among middle slides
    """
    if n_slides == 1:
        return [total_duration]

    title_dur = min(8.0, total_duration * 0.12)
    outro_dur = min(10.0, total_duration * 0.15)
    middle_total = max(0, total_duration - title_dur - outro_dur)
    middle_count = n_slides - 2
    mid_each = (middle_total / middle_count) if middle_count > 0 else 0

    durations = [title_dur] + [mid_each] * middle_count + [outro_dur]
    # Correct rounding
    diff = total_duration - sum(durations)
    durations[-2] += diff  # add leftover to last middle slide
    return durations


# ── Subtitle support ───────────────────────────────────────────────────────────

def _parse_srt(srt_path: str) -> list[dict]:
    """Parse SRT into list of {start, end, text} dicts (seconds)."""
    text = Path(srt_path).read_text(encoding="utf-8")
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n([\s\S]+?)(?=\n\n|\Z)"
    entries = []
    for m in re.finditer(pattern, text.strip()):
        def ts(s): 
            h, m_, rest = s.split(":")
            sec, ms = rest.split(",")
            return int(h)*3600 + int(m_)*60 + int(sec) + int(ms)/1000
        entries.append({
            "start": ts(m.group(2)),
            "end":   ts(m.group(3)),
            "text":  m.group(4).strip().replace("\n", " "),
        })
    return entries


def _make_subtitle_clips(srt_path: str, video_w: int, video_h: int) -> list:
    """Create a TextClip for each SRT subtitle entry."""
    entries = _parse_srt(srt_path)
    clips = []
    for entry in entries:
        dur = entry["end"] - entry["start"]
        if dur <= 0:
            continue
        txt_clip = (
            TextClip(
                entry["text"],
                fontsize=44,
                color="white",
                bg_color="rgba(0,0,0,0.6)",
                font="DejaVu-Sans-Bold",
                method="caption",
                size=(video_w - 120, None),
                align="center",
            )
            .set_start(entry["start"])
            .set_duration(dur)
            .set_position(("center", video_h - SUBTITLE_MARGIN - 60))
        )
        clips.append(txt_clip)
    return clips


def _make_simple_subtitle_clips(script_text: str, total_dur: float, video_w: int, video_h: int) -> list:
    """
    Fallback when no SRT is available:
    Split script into sentences and display them at even intervals.
    """
    sentences = re.split(r"(?<=[.!?])\s+", script_text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    if not sentences:
        return []

    dur_per = total_dur / len(sentences)
    clips = []
    for i, sentence in enumerate(sentences):
        # Truncate long sentences
        if len(sentence) > 120:
            sentence = sentence[:117] + "…"
        txt = (
            TextClip(
                sentence,
                fontsize=38,
                color="white",
                bg_color="rgba(0,0,0,0.55)",
                font="DejaVu-Sans",
                method="caption",
                size=(video_w - 200, None),
                align="center",
            )
            .set_start(i * dur_per)
            .set_duration(dur_per * 0.95)
            .set_position(("center", video_h - SUBTITLE_MARGIN - 50))
        )
        clips.append(txt)
    return clips


# ── STEP 20-22: Video assembly ─────────────────────────────────────────────────

def build_video(
    slide_paths: list[str],
    audio_path: str,
    script_text: str = "",
    srt_path: str | None = None,
    out_dir: str = "output",
    date_str: str | None = None,
) -> str:
    """
    Assemble final MP4 from slides + audio.
    Returns path to the output video.
    """
    if not slide_paths:
        raise ValueError("No slides provided")

    date_str = date_str or date.today().isoformat()
    video_dir = Path(out_dir) / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(video_dir / f"final_{date_str}.mp4")

    # Get audio duration
    total_dur = _audio_duration(audio_path)
    log.info(f"Audio duration: {total_dur:.1f}s  |  Slides: {len(slide_paths)}")

    # Calculate per-slide duration
    durations = _slide_durations(len(slide_paths), total_dur)

    # Build image clips (one per slide)
    log.info("Building slide clips …")
    slide_clips = []
    for i, (img_path, dur) in enumerate(zip(slide_paths, durations)):
        clip = (
            ImageClip(img_path)
            .set_duration(dur)
            .resize((VIDEO_W, VIDEO_H))
        )
        # Fade in on first slide, fade out on last
        if i == 0:
            clip = fadein(clip, TRANSITION_DURATION)
        if i == len(slide_paths) - 1:
            clip = fadeout(clip, TRANSITION_DURATION)
        slide_clips.append(clip)
        log.info(f"  Slide {i}: {Path(img_path).name}  ({dur:.1f}s)")

    # Concatenate with crossfades
    log.info("Concatenating clips …")
    video = concatenate_videoclips(slide_clips, method="compose")

    # Attach audio
    audio = AudioFileClip(audio_path).subclip(0, min(total_dur, video.duration))
    video = video.set_audio(audio)

    # STEP 23: Add subtitles
    log.info("Adding subtitles …")
    if srt_path and Path(srt_path).exists():
        log.info(f"  Using SRT: {srt_path}")
        sub_clips = _make_subtitle_clips(srt_path, VIDEO_W, VIDEO_H)
    elif script_text:
        log.info("  Using sentence-split subtitles")
        sub_clips = _make_simple_subtitle_clips(script_text, video.duration, VIDEO_W, VIDEO_H)
    else:
        sub_clips = []

    if sub_clips:
        video = CompositeVideoClip([video] + sub_clips)

    # Render
    log.info(f"Rendering video → {out_path} …")
    video.write_videofile(
        out_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp_audio.m4a",
        remove_temp=True,
        logger="bar",
        threads=os.cpu_count() or 4,
    )

    video.close()
    audio.close()

    log.info(f"✓ Video saved → {out_path}")
    return out_path


# ── STEP 23b: Whisper subtitle generation (production) ────────────────────────

def generate_srt_with_whisper(audio_path: str, out_dir: str = "output") -> str | None:
    """
    Use OpenAI Whisper to generate a word-level SRT file.
    Requires `whisper` to be installed: pip install openai-whisper
    Returns path to .srt file, or None if whisper is unavailable.
    """
    try:
        import whisper  # type: ignore
    except ImportError:
        log.warning("whisper not installed — skipping SRT generation")
        return None

    log.info("Running Whisper for subtitle generation …")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, word_timestamps=True)

    srt_lines = []
    idx = 1
    for segment in result["segments"]:
        start = segment["start"]
        end   = segment["end"]
        text  = segment["text"].strip()

        def fmt_ts(t: float) -> str:
            h = int(t // 3600)
            m = int((t % 3600) // 60)
            s = int(t % 60)
            ms = int((t % 1) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        srt_lines.append(f"{idx}\n{fmt_ts(start)} --> {fmt_ts(end)}\n{text}\n")
        idx += 1

    srt_path = str(Path(out_dir) / "subtitles" / "narration.srt")
    Path(srt_path).parent.mkdir(parents=True, exist_ok=True)
    Path(srt_path).write_text("\n".join(srt_lines), encoding="utf-8")
    log.info(f"✓ SRT saved → {srt_path}")
    return srt_path


# ── CLI test ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import glob

    slides   = sorted(glob.glob("output/images/*.png"))
    audio    = "output/audio/narration.mp3"
    srt_file = "output/subtitles/narration.srt"

    if not slides:
        print("No slides found. Run code_image.py first.")
        sys.exit(1)
    if not Path(audio).exists():
        print("No audio found. Run script_agent.py first.")
        sys.exit(1)

    # Optional whisper
    srt = generate_srt_with_whisper(audio) if not Path(srt_file).exists() else srt_file

    script_text = ""
    if Path("output/script.txt").exists():
        script_text = Path("output/script.txt").read_text()

    out = build_video(slides, audio, script_text=script_text, srt_path=srt)
    print(f"\nFinal video: {out}")
