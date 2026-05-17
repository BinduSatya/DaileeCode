"""
code_image.py
─────────────
STEP 18-19: Generate beautiful syntax-highlighted code images using Pygments + Pillow.
Output → output/images/code_*.png
"""

import json
import logging
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import ImageFormatter
from pygments.styles import get_style_by_name

logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")
log = logging.getLogger(__name__)

# ── Design constants ───────────────────────────────────────────────────────────
VIDEO_W, VIDEO_H = 1920, 1080
BG_COLOR      = (15, 17, 26)        # Deep dark background
CARD_COLOR    = (24, 28, 42)        # Slightly lighter card
ACCENT_GREEN  = (80, 200, 120)
ACCENT_BLUE   = (100, 160, 255)
ACCENT_ORANGE = (255, 160, 80)
TEXT_WHITE    = (230, 230, 240)
TEXT_MUTED    = (140, 145, 165)

DIFFICULTY_COLORS = {
    "Easy":   (0, 184, 163),
    "Medium": (255, 192, 30),
    "Hard":   (255, 55, 95),
}

PYGMENTS_STYLE = "monokai"


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/consola.ttf",       # Consolas (Windows built-in, great for code)
        "C:/Windows/Fonts/cour.ttf",           # Courier New regular
        "C:/Windows/Fonts/courbd.ttf",         # Courier New bold
        "C:/Windows/Fonts/arial.ttf",          # Arial fallback
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",  # Linux
        "/System/Library/Fonts/Menlo.ttc",     # macOS
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


# ── Slide builders ─────────────────────────────────────────────────────────────

def make_title_slide(problem: dict) -> Image.Image:
    """Slide 0 — Problem title + difficulty badge."""
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    diff = problem.get("difficulty", "Medium")
    diff_color = DIFFICULTY_COLORS.get(diff, ACCENT_BLUE)

    # Gradient strip at top
    for y in range(8):
        alpha = int(255 * (1 - y / 8))
        draw.line([(0, y), (VIDEO_W, y)], fill=diff_color)

    # LeetCode logo text
    font_brand = _load_font(28)
    draw.text((60, 80), "LeetCode Daily Challenge", font=font_brand, fill=TEXT_MUTED)

    # Problem number + title
    font_id = _load_font(52, bold=True)
    font_title = _load_font(72, bold=True)

    title = problem["title"]
    # Wrap long titles
    wrapped = textwrap.fill(title, width=40)
    y_title = VIDEO_H // 2 - 120
    for line in wrapped.split("\n"):
        draw.text((60, y_title), line, font=font_title, fill=TEXT_WHITE)
        y_title += 90

    # Difficulty badge
    badge_x, badge_y = 60, y_title + 30
    badge_text = f"  {diff}  "
    bbox = draw.textbbox((badge_x, badge_y), badge_text, font=_load_font(36, bold=True))
    draw.rounded_rectangle(
        [bbox[0] - 10, bbox[1] - 8, bbox[2] + 10, bbox[3] + 8],
        radius=8,
        fill=diff_color,
    )
    draw.text((badge_x, badge_y), badge_text, font=_load_font(36, bold=True), fill=(10, 10, 10))

    # Tags
    tags = problem.get("tags", [])[:4]
    tag_x = badge_x + 200
    for tag in tags:
        tag_font = _load_font(28)
        bbox = draw.textbbox((tag_x, badge_y + 4), f" {tag} ", font=tag_font)
        draw.rounded_rectangle(
            [bbox[0] - 6, bbox[1] - 4, bbox[2] + 6, bbox[3] + 4],
            radius=6,
            fill=CARD_COLOR,
        )
        draw.text((tag_x, badge_y + 4), f" {tag} ", font=tag_font, fill=ACCENT_BLUE)
        tag_x += bbox[2] - bbox[0] + 16

    # URL bottom right
    font_url = _load_font(24)
    draw.text((VIDEO_W - 520, VIDEO_H - 60), problem["url"], font=font_url, fill=TEXT_MUTED)

    return img


def make_problem_slide(problem: dict) -> Image.Image:
    """Slide 1 — Problem description (first 600 chars)."""
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_header = _load_font(48, bold=True)
    font_body   = _load_font(30)

    draw.text((60, 50), "Problem Statement", font=font_header, fill=TEXT_WHITE)
    draw.line([(60, 116), (VIDEO_W - 60, 116)], fill=ACCENT_BLUE, width=2)

    # Word-wrap the description
    desc = problem.get("description", "")[:1200]
    wrapped = textwrap.fill(desc, width=88)
    y = 140
    for line in wrapped.split("\n")[:22]:
        draw.text((60, y), line, font=font_body, fill=TEXT_WHITE)
        y += 40

    return img


def make_code_slide(code: str, title: str = "Solution") -> Image.Image:
    """Slide 2+ — Syntax-highlighted Python code using Pygments."""
    # Pygments → PNG bytes
    formatter = ImageFormatter(
        style=PYGMENTS_STYLE,
        font_name="Courier New",
        font_size=22,
        line_numbers=True,
        line_pad=4,
        image_pad=24,
    )
    lexer = PythonLexer()
    png_bytes = highlight(code, lexer, formatter)

    code_img = Image.open(__import__("io").BytesIO(png_bytes)).convert("RGB")

    # Compose onto video frame
    frame = Image.new("RGB", (VIDEO_W, VIDEO_H), BG_COLOR)
    draw = ImageDraw.Draw(frame)

    font_header = _load_font(44, bold=True)
    draw.text((60, 40), title, font=font_header, fill=TEXT_WHITE)
    draw.line([(60, 100), (VIDEO_W - 60, 100)], fill=ACCENT_GREEN, width=2)

    # Scale code image to fit (max 1780×900)
    max_w, max_h = VIDEO_W - 140, VIDEO_H - 140
    ratio = min(max_w / code_img.width, max_h / code_img.height)
    if ratio < 1:
        new_size = (int(code_img.width * ratio), int(code_img.height * ratio))
        code_img = code_img.resize(new_size, Image.LANCZOS)

    # Center horizontally
    x_off = (VIDEO_W - code_img.width) // 2
    y_off = (VIDEO_H - code_img.height) // 2 + 30
    frame.paste(code_img, (x_off, y_off))

    return frame


def make_complexity_slide(explanation: str) -> Image.Image:
    """Slide — Time & Space complexity summary."""
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_header = _load_font(56, bold=True)
    font_body   = _load_font(34)

    draw.text((60, 50), "Complexity Analysis", font=font_header, fill=TEXT_WHITE)
    draw.line([(60, 128), (VIDEO_W - 60, 128)], fill=ACCENT_ORANGE, width=2)

    # Extract complexity lines from explanation
    import re
    time_match  = re.search(r"[Tt]ime[^:]*:?\s*(O\([^)]+\)[^\n]*)", explanation)
    space_match = re.search(r"[Ss]pace[^:]*:?\s*(O\([^)]+\)[^\n]*)", explanation)

    y = 200
    for label, match, color in [
        ("⏱  Time Complexity",  time_match,  ACCENT_GREEN),
        ("💾  Space Complexity", space_match, ACCENT_BLUE),
    ]:
        draw.text((80, y), label, font=_load_font(42, bold=True), fill=color)
        value = match.group(1).strip() if match else "See explanation"
        draw.text((100, y + 56), value, font=font_body, fill=TEXT_WHITE)
        y += 160

    # Brief explanation excerpt
    clean = re.sub(r"\*+", "", explanation)
    excerpt = textwrap.fill(clean[:400], width=80)
    draw.text((80, y + 20), "Explanation:", font=_load_font(36, bold=True), fill=TEXT_MUTED)
    y_ex = y + 70
    for line in excerpt.split("\n")[:8]:
        draw.text((80, y_ex), line, font=_load_font(28), fill=TEXT_WHITE)
        y_ex += 38

    return img


def make_outro_slide(problem: dict) -> Image.Image:
    """Final slide — subscribe CTA."""
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_big  = _load_font(80, bold=True)
    font_med  = _load_font(40)
    font_sm   = _load_font(30)

    cx = VIDEO_W // 2

    def centered(y: int, text: str, font, fill):
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((VIDEO_W - w) // 2, y), text, font=font, fill=fill)

    centered(200,  "Thanks for watching! 🎉",  font_big, TEXT_WHITE)
    centered(320,  f"Problem: {problem['title']}", font_med, ACCENT_BLUE)
    centered(420,  "👍  Like  •  🔔  Subscribe  •  💬  Comment your approach", font_med, ACCENT_GREEN)
    centered(530,  problem["url"], font_sm, TEXT_MUTED)
    centered(VIDEO_H - 100, "New LeetCode Daily Solution every day!", font_sm, TEXT_MUTED)

    return img


# ── Main runner ────────────────────────────────────────────────────────────────

def generate_all_slides(problem: dict, solution: dict, out_dir: str = "output") -> list[str]:
    """Generate all slides and return list of image paths."""
    img_dir = Path(out_dir) / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    slides = []

    def save(img: Image.Image, name: str) -> str:
        path = img_dir / name
        img.save(str(path), "PNG")
        log.info(f"  ✓ {path.name}")
        return str(path)

    log.info("Generating slides …")
    slides.append(save(make_title_slide(problem),           "00_title.png"))
    slides.append(save(make_problem_slide(problem),         "01_problem.png"))
    slides.append(save(make_code_slide(solution["code"], "Python Solution"), "02_code.png"))
    slides.append(save(make_complexity_slide(solution["explanation"]),       "03_complexity.png"))
    slides.append(save(make_outro_slide(problem),           "04_outro.png"))

    log.info(f"✓ {len(slides)} slides saved → {img_dir}")
    return slides


# ── CLI test ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    for path in ["output/problem.json", "output/solution.json"]:
        if not Path(path).exists():
            print(f"Missing {path}")
            sys.exit(1)

    problem  = json.loads(Path("output/problem.json").read_text())
    solution = json.loads(Path("output/solution.json").read_text())

    slides = generate_all_slides(problem, solution)
    print(f"Generated {len(slides)} slides")
