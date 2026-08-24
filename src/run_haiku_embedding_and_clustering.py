#!/usr/bin/env python3
"""
Embed summary_haiku texts and cluster them, with silhouette-based k selection.
Writes a summary report to reports/haiku_cluster_results.json and a CSV.

Run with:
    PYTHONPATH=$PWD python src/run_haiku_embedding_and_clustering.py
"""

from __future__ import annotations

import json
import csv
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.run_vector_pipeline import run_embedding_and_clustering  # noqa: E402
from src.store import load_store  # noqa: E402


REPORT_JSON = Path("reports/haiku_cluster_results.json")
ARTICLES_CSV = Path("reports/haiku_cluster_articles.csv")


def authors_to_str(authors) -> str:
    if authors is None:
        return ""
    if isinstance(authors, list):
        return " & ".join(str(x) for x in authors if str(x).strip())
    return str(authors)


def write_articles_csv(output_path: Path) -> int:
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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "cluster_haiku_summary",
        "year",
        "volume",
        "issue",
        "article_number",
        "editorial",
        "category",
        "authors",
        "title",
        "summary_haiku",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for a in articles:
            writer.writerow(
                {
                    "cluster_haiku_summary": a.cluster_haiku_summary
                    if a.cluster_haiku_summary is not None
                    else "",
                    "year": a.year if a.year is not None else "",
                    "volume": a.volume if a.volume is not None else "",
                    "issue": a.issue if a.issue is not None else "",
                    "article_number": a.article_number if a.article_number is not None else "",
                    "editorial": a.editorial or "",
                    "category": a.category or "",
                    "authors": authors_to_str(a.authors),
                    "title": a.title or "",
                    "summary_haiku": a.summary_haiku or "",
                }
            )
    return len(articles)


def main() -> None:
    print("=== Step 1: Embed summary_haiku (all-MiniLM-L6-v2) ===")
    result = run_embedding_and_clustering(
        source_field="summary_haiku",
        embedding_field="embedding_haiku_summary",
        cluster_field="cluster_haiku_summary",
        model_name="all-MiniLM-L6-v2",
        k=None,   # auto-select via silhouette
    )
    print(f"  Articles embedded : {result['n_articles']}")
    print(f"  Embedding dim     : {result['embedding_dim']}")
    print(f"  Best k (silhouette): {result['k']}")

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"  Report saved      : {REPORT_JSON}")

    print("\n=== Step 2: Write articles CSV with cluster assignments ===")
    n = write_articles_csv(ARTICLES_CSV)
    print(f"  Rows written: {n}")
    print(f"  CSV saved   : {ARTICLES_CSV}")

    print("\nDone.")


if __name__ == "__main__":
    main()
