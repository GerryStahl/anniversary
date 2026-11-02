#!/usr/bin/env python3
import csv
from collections import Counter
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.cluster_vectors import cluster_kmeans, load_vector_matrix
from src.store import load_store, save_store

K = 7
OUT = Path("reports/haiku_7_clusters.csv")

store = load_store()
ids, matrix = load_vector_matrix(store, "embedding_haiku_summary")
labels = cluster_kmeans(matrix, n_clusters=K)
for aid, label in zip(ids, labels):
    store[aid].cluster_haiku_summary = int(label)
save_store(store)

def a2s(a):
    if a is None:
        return ""
    if isinstance(a, list):
        return " & ".join(str(x) for x in a if str(x).strip())
    return str(a)

articles = sorted(
    store.values(),
    key=lambda a: (a.year or 9999, a.volume or 999, a.issue or 999, a.article_number or 999, a.id),
)

OUT.parent.mkdir(parents=True, exist_ok=True)
fields = ["cluster_haiku_summary", "year", "volume", "issue", "article_number",
          "editorial", "category", "authors", "title", "summary_haiku"]
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for a in articles:
        w.writerow({
            "cluster_haiku_summary": a.cluster_haiku_summary if a.cluster_haiku_summary is not None else "",
            "year": a.year or "", "volume": a.volume or "", "issue": a.issue or "",
            "article_number": a.article_number or "", "editorial": a.editorial or "",
            "category": a.category or "", "authors": a2s(a.authors),
            "title": a.title or "", "summary_haiku": a.summary_haiku or "",
        })

print(f"Written {len(articles)} rows to {OUT}")
counts = Counter(a.cluster_haiku_summary for a in articles if a.cluster_haiku_summary is not None)
for k in sorted(counts):
    print(f"  cluster {k}: {counts[k]} articles")
