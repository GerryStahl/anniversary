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


def build_cluster_haiku_summary_csv(output_path: Path) -> Path:
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
                "Cluster",
                "Editorial",
                "Category",
                "Volume",
                "Issue",
                "Article_Number",
                "Authors",
                "Title",
            ]
        )
        for a in articles:
            writer.writerow(
                [
                    a.cluster_haiku_summary if a.cluster_haiku_summary is not None else "",
                    a.editorial or "",
                    a.category or "",
                    a.volume if a.volume is not None else "",
                    a.issue if a.issue is not None else "",
                    a.article_number if a.article_number is not None else "",
                    authors_to_str(a.authors),
                    a.title or "",
                ]
            )

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build reports/cluster_haiku_summary.csv from data/processed/ijcscl.pkl"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/cluster_haiku_summary.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    out_path = build_cluster_haiku_summary_csv(Path(args.output))
    print("CSV_PATH", out_path)


if __name__ == "__main__":
    main()
