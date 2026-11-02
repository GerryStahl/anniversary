#!/usr/bin/env python3
"""Re-cluster existing embedding_haiku_summary vectors with k=5 and write CSV."""

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.cluster_vectors import cluster_kmeans, load_vector_matrix  # noqa: E402
from src.store import load_store, save_store  # noqa: E402

K = 5
OUT_CSV = Path("reports/haiku_4_clusters.csv")  # "4" = first k > 4 split


def authors_to_str(authors) -> str:
    if authors is None:
        return ""
    if isinstance(authors, list):
        return " & ".join(str(x) for x in authors if str(x).strip())
    return str(authors)


def main() -> None:
    store = load_store()

    article_ids, matrix = load_vector_matrix(store, "embedding_haiku_summary")
    print(f"Loaded {len(article_ids)} vectors, dim={matrix.shape[1]}")

    labels = cluster_kmeans(matrix, n_clusters=K)
    print(f"Clustered into k={K}")

    for article_id, label in zip(article_ids, labels):
        store[article_id].cluster_haiku_summary = int(label)

    save_store(store)
    print("Store saved")

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

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "cluster_haiku_summary",
        "year", "volume", "issue", "article_number",
        "editorial", "category", "authors", "title", "summary_haiku",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for a in articles:
            writer.writerow({
                "cluster_haiku_summary": a.cluster_haiku_summary if a.cluster_haiku_summary is not None else "",
                "year": a.year if a.year is not None else "",
                "volume": a.volume if a.volume is not None else "",
                "issue": a.issue if a.issue is not None else "",
                "article_number": a.article_number if a.article_number is not None else "",
                "editorial": a.editorial or "",
                "category": a.category or "",
                "authors": authors_to_str(a.authors),
                "title": a.title or "",
                "summary_haiku": a.summary_haiku or "",
            })

    print(f"CSV written: {OUT_CSV} ({len(articles)} rows)")


if __name__ == "__main__":
    main()
