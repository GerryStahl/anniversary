import argparse
import csv
import difflib
import os
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError as exc:  # pragma: no cover - friendly CLI failure
    raise SystemExit(
        "Missing dependency 'anthropic'. Install with `pip install -r requirements.txt`."
    ) from exc

from src.store import load_store, save_store
from src.summarize_Claude import (
    DEFAULT_MODEL,
    format_authors,
    selected_article_ids,
    summarize_article_with_claude,
)


DEFAULT_OUTPUT = Path("reports/summary_comparison.csv")


def diff_score(left: str, right: str) -> float:
    """Return a 0-100 diff score where 0 means identical and 100 means very different."""
    similarity = difflib.SequenceMatcher(None, left.lower(), right.lower()).ratio()
    return round((1.0 - similarity) * 100.0, 2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Ollama and Claude summaries for a small set of articles."
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
        default=5,
        help="Limit the number of articles to compare (default: 5)",
    )
    parser.add_argument(
        "--ids",
        default=None,
        help="Comma-separated list of article IDs to compare",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Re-generate Claude summaries even if already cached in the store",
    )
    return parser.parse_args()


def main():
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

    # Build comparison data
    comparisons = []
    for article_id in article_ids:
        article = store[article_id]
        ollama_summary = article.summary_ollama or "[No Ollama summary available]"

        authors_str = format_authors(article.authors)

        if article.summary_haiku and not args.overwrite:
            claude_summary = article.summary_haiku
        else:
            claude_summary = summarize_article_with_claude(
                client=client,
                article=article,
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            )
            article.summary_haiku = claude_summary

        summary_diff_score = diff_score(ollama_summary, claude_summary)

        comparisons.append({
            "Article ID": article_id,
            "Title": article.title or "[No title]",
            "Authors": authors_str,
            "Ollama (llama3.1:8b) Summary": ollama_summary,
            "Claude Haiku Summary": claude_summary,
            "Summary Diff Score": summary_diff_score,
        })

    # Persist any newly generated Claude summaries back to the store.
    save_store(store)

    # Write to CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Article ID",
            "Title",
            "Authors",
            "Ollama (llama3.1:8b) Summary",
            "Claude Haiku Summary",
            "Summary Diff Score",
        ])
        writer.writeheader()
        writer.writerows(comparisons)

    print(f"Comparison spreadsheet created: {output_path}")
    print(f"Total comparisons: {len(comparisons)}")
    for comp in comparisons:
        print(f"\n{comp['Article ID']}: {comp['Title'][:60]}...")
        print(f"  Ollama length: {len(comp['Ollama (llama3.1:8b) Summary'])} chars")
        print(f"  Claude length: {len(comp['Claude Haiku Summary'])} chars")
        print(f"  Diff score: {comp['Summary Diff Score']}")


if __name__ == "__main__":
    main()
