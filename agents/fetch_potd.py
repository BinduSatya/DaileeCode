"""
fetch_potd.py
─────────────
Fetches LeetCode's Problem of the Day (POTD) using the public GraphQL API.
Returns a structured dict with title, slug, difficulty, description, and examples.
"""

import json
import logging
import re
import time
from datetime import date
from pathlib import Path
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")
log = logging.getLogger(__name__)

GRAPHQL_URL = "https://leetcode.com/graphql"

# ── GraphQL query ──────────────────────────────────────────────────────────────
POTD_QUERY = """
query questionOfToday {
  activeDailyCodingChallengeQuestion {
    date
    link
    question {
      questionId
      title
      titleSlug
      difficulty
      content
      exampleTestcases
      topicTags { name }
      hints
    }
  }
}
"""

DETAIL_QUERY = """
query questionDetail($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    title
    titleSlug
    difficulty
    content
    exampleTestcases
    sampleTestCase
    metaData
    codeSnippets { lang langSlug code }
    topicTags { name }
    hints
  }
}
"""

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (LeetCode POTD Bot)",
    "Referer": "https://leetcode.com",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _graphql(query: str, variables: Optional[dict] = None) -> dict:
    payload = {"query": query, "variables": variables or {}}
    resp = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise ValueError(f"GraphQL errors: {data['errors']}")
    return data["data"]


def _strip_html(html: str) -> str:
    """Very lightweight HTML → plain-text (no external dep)."""
    text = re.sub(r"<[^>]+>", "", html)
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    text = text.replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def fetch_potd() -> dict:
    """Return today's POTD as a clean Python dict."""
    log.info("Fetching POTD from LeetCode …")
    data = _graphql(POTD_QUERY)
    challenge = data["activeDailyCodingChallengeQuestion"]

    slug = challenge["question"]["titleSlug"]
    potd_date = challenge["date"]

    log.info(f"POTD date={potd_date}  slug={slug}")

    # Fetch full detail (includes code snippets)
    detail = _graphql(DETAIL_QUERY, {"titleSlug": slug})["question"]

    # Pick Python3 snippet (fallback to first available)
    snippets = {s["langSlug"]: s["code"] for s in (detail.get("codeSnippets") or [])}
    starter_code = (
        snippets.get("python3")
        or snippets.get("python")
        or next(iter(snippets.values()), "")
    )

    # Parse metaData for function signature info
    try:
        meta = json.loads(detail.get("metaData") or "{}")
    except json.JSONDecodeError:
        meta = {}

    problem = {
        "date": potd_date,
        "id": detail["questionId"],
        "title": detail["title"],
        "slug": detail["titleSlug"],
        "difficulty": detail["difficulty"],
        "url": f"https://leetcode.com/problems/{slug}/",
        "description": _strip_html(detail.get("content") or ""),
        "example_testcases": detail.get("exampleTestcases") or "",
        "sample_testcase": detail.get("sampleTestCase") or "",
        "tags": [t["name"] for t in (detail.get("topicTags") or [])],
        "hints": detail.get("hints") or [],
        "starter_code": starter_code,
        "meta": meta,
    }

    log.info(f"✓ Fetched: [{problem['difficulty']}] {problem['title']}")
    return problem


def save_problem(problem: dict, out_dir: str = "output") -> Path:
    """Persist problem JSON for downstream steps."""
    path = Path(out_dir) / "problem.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(problem, indent=2, ensure_ascii=False))
    log.info(f"Saved problem → {path}")
    return path


# ── CLI test ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    problem = fetch_potd()
    save_problem(problem)
    print(json.dumps(problem, indent=2))
