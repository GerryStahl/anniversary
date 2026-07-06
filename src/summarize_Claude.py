#!/usr/bin/env python3
"""Generate Claude summaries using the same prompt structure as Ollama."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from anthropic import Anthropic
except ImportError as exc:  # pragma: no cover - friendly CLI failure
    raise SystemExit(
        "Missing dependency 'anthropic'. Install with `pip install -r requirements.txt`."
    ) from exc

from src.summarize import (  # noqa: E402
    SUMMARIZATION_SYSTEM_PROMPT,
    build_summarization_prompt,
    clean_summary,
)
from src.store import load_store, save_store  # noqa: E402


DEFAULT_MODEL = "claude-haiku-4-5"
DEFAULT_OUTPUT = Path("reports/claude_summaries.csv")


def format_authors(authors: object) -> str:
    if isinstance(authors, list):
        return " & ".join(str(author) for author in authors if str(author).strip())
    if authors:
        return str(authors)
    return "Unknown"


def extract_text(response: object) -> str:
    blocks = getattr(response, "content", None) or []
    parts = []
    for block in blocks:
        if getattr(block, "type", None) == "text" and getattr(block, "text", ""):
            parts.append(block.text)
    return clean_summary(" ".join(parts))


def summarize_article_with_claude(
    client: Anthropic,
    article,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 220,
) -> str:
    user_prompt = build_summarization_prompt(article)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=SUMMARIZATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return extract_text(response)


def selected_article_ids(
    store: dict,
    ids: Optional[list[str]] = None,
    limit: Optional[int] = None,
) -> list[str]:
    article_ids = ids if ids else sorted(store.keys())
    if limit is not None:
        article_ids = article_ids[:limit]
    return article_ids


def write_csv(rows: Iterable[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "Article ID",
                "Title",
                "Authors",
                "Claude Summary",
                "Word Count",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Claude summaries using the same system prompt and article "
            "prompt structure as the Ollama summarizer."
        )
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Claude model name to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature passed to Claude (default: 0.2)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=220,
        help="Maximum tokens to request from Claude (default: 220)",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"CSV output path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of articles to summarize",
    )
    parser.add_argument(
        "--ids",
        default=None,
        help="Comma-separated list of article IDs to summarize",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Re-generate even if summary_haiku already exists in the store",
    )
    return parser.parse_args()


def main() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set.")

    args = parse_args()
    client = Anthropic(api_key=api_key)

    store = load_store()
    ids = None
    if args.ids:
        ids = [item.strip() for item in args.ids.split(",") if item.strip()]

    article_ids = selected_article_ids(store, ids=ids, limit=args.limit)

    rows = []
    generated = 0
    cached = 0
    for article_id in article_ids:
        article = store[article_id]
        if not article.fulltext:
            continue

        if article.summary_haiku and not args.overwrite:
            summary = article.summary_haiku
            cached += 1
        else:
            summary = summarize_article_with_claude(
                client=client,
                article=article,
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            )
            article.summary_haiku = summary
            generated += 1

        authors = format_authors(article.authors)
        rows.append(
            {
                "Article ID": article_id,
                "Title": article.title or "[No title]",
                "Authors": authors,
                "Claude Summary": summary,
                "Word Count": len(summary.split()),
            }
        )

        print(f"{article_id}: {article.title or '[No title]'}")
        print(f"  Summary length: {len(summary)} chars")

    # Persist newly generated summary_haiku values to pkl/json.
    if generated:
        save_store(store)
        print(f"\nPersisted {generated} new Claude summaries to store ({cached} already cached).")

    output_path = Path(args.output)
    write_csv(rows, output_path)
    print(f"\nClaude summary CSV created: {output_path}")
    print(f"Total summaries: {len(rows)}")


if __name__ == "__main__":
    main()