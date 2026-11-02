#!/usr/bin/env python3
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from src.cluster_vectors import choose_k_by_silhouette, load_vector_matrix
from src.store import load_store
store = load_store()
ids, matrix = load_vector_matrix(store, "embedding_haiku_summary")
scores = choose_k_by_silhouette(matrix, k_values=range(2, 41))
best_k = max(scores, key=scores.get)
print(f"{'k':>4}  {'silhouette':>10}  {'':}")
for k in sorted(scores):
    bar = "#" * int(scores[k] * 400)
    marker = " <-- best" if k == best_k else ""
    print(f"  {k:2d}  {scores[k]:.4f}  {bar}{marker}")
