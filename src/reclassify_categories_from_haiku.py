#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from anthropic import Anthropic
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency 'anthropic'. Install with `pip install -r requirements.txt`."
    ) from exc

from src.store import load_store, save_store  # noqa: E402


DEFAULT_MODEL = "claude-haiku-4-5"
DEFAULT_OUTPUT = Path("reports/categories_from_haiku_with_g.csv")


CATEGORY_PROMPT = """
You classify IJCSCL articles into exactly one category based on title and summary.

Return only one letter:
a. design of collaboration
b. design of technology to support learning
c. analysis of interaction among students
d. measurement of learning
f. none of the above
g. CSCL theory

Definitions:
- g (CSCL theory): primarily conceptual/theoretical framing, synthesis, or theory building about CSCL itself.
- d (measurement of learning): focus on assessment/measurement/modeling of outcomes or learning processes.
- c (analysis of interaction): primary focus on discourse/interaction/process analysis among learners.
- b (design of technology): primary focus on tools/platforms/technical supports.
- a (design of collaboration): primary focus on scripting/orchestration/task/pedagogical collaboration design.

Choose the single best primary category. Return one lowercase letter only.
""".strip()


def normalize_category(text: str) -> str:
    cleaned = (text or "").strip().lower()
    for ch in cleaned:
        if ch in {"a", "b", "c", "d", "e", "f", "g"}:
            return ch
    return "f"


def build_user_prompt(article) -> str:
    title = article.title or ""
    summary = article.summary_haiku or ""
    return f"""Title: {title}
Summary: {summary}""".strip()


def classify_with_haiku(client: Anthropic, article, model: str) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=10,
        temperature=0.0,
        system=CATEGORY_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(article)}],
    )

    parts = []
    for block in getattr(response, "content", []) or []:
        if getattr(block, "type", None) == "text" and getattr(block, "text", ""):
            parts.append(block.text)

    return normalize_category(" ".join(parts))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Re-classify all articles using summary_haiku with added category g (CSCL theory)."
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Claude model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output CSV path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=25,
        help="Save store every N reclassifications (default: 25)",
    )
    return parser.parse_args()


def main() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set.")

    args = parse_args()
    client = Anthropic(api_key=api_key)

    store = load_store()
    articles = sorted(
        store.values(),
        key=lambda a: (
            a.year if isinstance(a.year, int) else 9999,
            a.volume if isinstance(a.volume, int) else 999,
            a.issue if isinstance(a.issue, int) else 999,
            a.article_number if isinstance(a.article_number, int) else 999,
            a.id,
        ),
    )

    changed = 0
    processed = 0
    dirty_since_save = 0
    rows = []
    counts = Counter()

    for idx, article in enumerate(articles, start=1):
        old = article.category

        # User rule: any non-null editorial value => category e
        if (article.editorial or "").strip():
            new_cat = "e"
        else:
            new_cat = classify_with_haiku(client, article, model=args.model)

        article.category = new_cat
        counts[new_cat] += 1
        processed += 1

        if old != new_cat:
            changed += 1
            dirty_since_save += 1

        rows.append(
            {
                "id": article.id,
                "year": article.year if article.year is not None else "",
                "volume": article.volume if article.volume is not None else "",
                "issue": article.issue if article.issue is not None else "",
                "article_number": article.article_number if article.article_number is not None else "",
                "editorial": article.editorial or "",
                "old_category": old or "",
                "new_category": new_cat,
                "authors": " & ".join(article.authors) if isinstance(article.authors, list) else (article.authors or ""),
                "title": article.title or "",
                "summary_haiku": article.summary_haiku or "",
            }
        )

        if dirty_since_save and args.checkpoint_every > 0 and dirty_since_save % args.checkpoint_every == 0:
            save_store(store)
            print(f"CHECKPOINT {idx}/{len(articles)}")
            dirty_since_save = 0

    save_store(store)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "year",
        "volume",
        "issue",
        "article_number",
        "editorial",
        "old_category",
        "new_category",
        "authors",
        "title",
        "summary_haiku",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("TOTAL", processed)
    print("CHANGED", changed)
    print("OUT", output_path)
    print("COUNTS")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")


if __name__ == "__main__":
    main()
