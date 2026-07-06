import numpy as np
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score

from .store import ArticlesStore


def load_vector_matrix(store: ArticlesStore, embedding_field: str) -> tuple[list[str], np.ndarray]:
    """
    Pull vectors from the store and return aligned article_ids and matrix.
    """
    article_ids: list[str] = []
    vectors: list[list[float]] = []
    expected_dim: int | None = None

    for article_id, article in store.items():
        vector = getattr(article, embedding_field, None)
        if vector is None:
            continue

        vector_list = list(vector)
        if expected_dim is None:
            expected_dim = len(vector_list)
        elif len(vector_list) != expected_dim:
            raise ValueError(
                f"Inconsistent vector dimensions in '{embedding_field}': "
                f"expected {expected_dim}, got {len(vector_list)} for {article_id}."
            )

        article_ids.append(article_id)
        vectors.append(vector_list)

    if not vectors:
        return [], np.empty((0, 0), dtype=float)

    matrix = np.asarray(vectors, dtype=float)
    return article_ids, matrix


def cluster_kmeans(
    matrix: np.ndarray,
    n_clusters: int,
    random_state: int = 42,
) -> np.ndarray:
    """
    KMeans clustering on embedding vectors.
    """
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init="auto")
    return model.fit_predict(matrix)


def choose_k_by_silhouette(
    matrix: np.ndarray,
    k_values: range = range(2, 15),
) -> dict[int, float]:
    """
    Score candidate k values using cosine-distance silhouette score.
    """
    if len(matrix) < 3:
        return {}

    scores: dict[int, float] = {}
    for k in k_values:
        if k >= len(matrix):
            continue

        labels = cluster_kmeans(matrix, n_clusters=k)
        if len(set(labels)) < 2:
            continue

        scores[k] = float(silhouette_score(matrix, labels, metric="cosine"))
    return scores


def cluster_agglomerative(
    matrix: np.ndarray,
    n_clusters: int,
) -> np.ndarray:
    """
    Hierarchical clustering using cosine distance and average linkage.
    """
    model = AgglomerativeClustering(
        n_clusters=n_clusters,
        metric="cosine",
        linkage="average",
    )
    return model.fit_predict(matrix)