#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

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
DEFAULT_CHECKPOINT_EVERY = 10
DEFAULT_FAILURE_REPORT = Path("reports/missing_haiku_summary_failures.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate summary_haiku for articles where it is currently null/empty."
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Claude model to use (default: {DEFAULT_MODEL})",
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
        "--limit",
        type=int,
        default=None,
        help="Optional cap on the number of missing summaries to generate",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=DEFAULT_CHECKPOINT_EVERY,
        help="Save the store after every N new summaries (default: 10)",
    )
    parser.add_argument(
        "--failure-report",
        default=str(DEFAULT_FAILURE_REPORT),
        help=f"CSV for per-article failures (default: {DEFAULT_FAILURE_REPORT})",
    )
    return parser.parse_args()


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


def write_failures_csv(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["id", "year", "volume", "issue", "article_number", "title", "error"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set.")

    args = parse_args()
    client = Anthropic(api_key=api_key)
    store = load_store()

    targets = [
        article
        for article in store.values()
        if not (article.summary_haiku or "").strip() and (article.fulltext or "").strip()
    ]
    targets.sort(
        key=lambda article: (
            article.year if isinstance(article.year, int) else 9999,
            article.volume if isinstance(article.volume, int) else 999,
            article.issue if isinstance(article.issue, int) else 999,
            article.article_number if isinstance(article.article_number, int) else 999,
            article.id,
        )
    )

    if args.limit is not None:
        targets = targets[: args.limit]

    print(f"TARGETS {len(targets)}")
    if not targets:
        print("No missing summary_haiku values found.")
        return

    generated = 0
    failures: list[dict] = []
    dirty = False

    for index, article in enumerate(targets, start=1):
        print(f"[{index}/{len(targets)}] {article.id} :: {article.title or '[No title]'}")
        try:
            summary = summarize_article_with_claude(
                client=client,
                article=article,
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            )
            article.summary_haiku = summary
            generated += 1
            dirty = True
            print(f"  OK {len(summary.split())} words")
        except Exception as exc:
            failures.append(
                {
                    "id": article.id,
                    "year": article.year,
                    "volume": article.volume,
                    "issue": article.issue,
                    "article_number": article.article_number,
                    "title": article.title,
                    "error": str(exc),
                }
            )
            print(f"  FAIL {exc}")

        if dirty and args.checkpoint_every > 0 and generated % args.checkpoint_every == 0:
            save_store(store)
            dirty = False
            print(f"  CHECKPOINT saved after {generated} new summaries")

    if dirty:
        save_store(store)
        print("FINAL CHECKPOINT saved")

    failure_report = Path(args.failure_report)
    write_failures_csv(failures, failure_report)

    print(f"GENERATED {generated}")
    print(f"FAILED {len(failures)}")
    print(f"FAILURE_REPORT {failure_report}")


if __name__ == "__main__":
    main()
