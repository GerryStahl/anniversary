import argparse
import csv
from pathlib import Path

from src.store import load_store


def authors_to_str(authors) -> str:
    if authors is None:
        return ""
    if isinstance(authors, list):
        return " & ".join(str(x) for x in authors)
    return str(authors)


def build_articles_csv(output_path: Path) -> Path:
    store = load_store()
    articles = list(store.values())
    articles.sort(
        key=lambda a: (
            a.volume if a.volume is not None else 9999,
            a.issue if a.issue is not None else 9999,
            a.article_number if a.article_number is not None else 9999,
            a.id,
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "volume",
                "issue",
                "article_number",
                "title",
                "authors",
                "category",
                "summary_ollama",
                "summary_haiku",
            ]
        )
        for a in articles:
            writer.writerow(
                [
                    a.volume if a.volume is not None else "",
                    a.issue if a.issue is not None else "",
                    a.article_number if a.article_number is not None else "",
                    a.title or "",
                    authors_to_str(a.authors),
                    a.category or "",
                    a.summary_ollama or "",
                    a.summary_haiku or "",
                ]
            )

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build reports/articles.csv from data/processed/ijcscl.pkl"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/articles.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    out_path = build_articles_csv(Path(args.output))
    print("CSV_PATH", out_path)


if __name__ == "__main__":
    main()
