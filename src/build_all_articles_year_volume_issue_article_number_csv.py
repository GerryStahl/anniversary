import argparse
import csv
from pathlib import Path

from src.store import load_store


FIELDS = [
    "year",
    "volume",
    "issue",
    "article_number",
    "editorial",
    "authors",
    "title",
]


def format_authors(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " & ".join(str(v).strip() for v in value if str(v).strip())
    return str(value)


def sort_key(article):
    return (
        article.year if isinstance(article.year, int) else 9999,
        article.volume if isinstance(article.volume, int) else 999,
        article.issue if isinstance(article.issue, int) else 999,
        article.article_number if isinstance(article.article_number, int) else 999,
        (article.title or "").lower(),
        article.id,
    )


def build_csv(output_path: Path) -> int:
    store = load_store()
    rows = []

    for article in sorted(store.values(), key=sort_key):
        rows.append(
            {
                "year": article.year if article.year is not None else "",
                "volume": article.volume if article.volume is not None else "",
                "issue": article.issue if article.issue is not None else "",
                "article_number": article.article_number if article.article_number is not None else "",
                "editorial": article.editorial or "",
                "authors": format_authors(article.authors),
                "title": article.title or "",
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build all_articles_year_volume_issue_article_number_editorial_authors_title.csv from store"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/all_articles_year_volume_issue_article_number_editorial_authors_title.csv"),
    )
    args = parser.parse_args()

    total = build_csv(args.output)
    print("CSV_PATH", args.output)
    print("TOTAL_ROWS", total)


if __name__ == "__main__":
    main()
