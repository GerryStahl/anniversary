from typing import Optional

from .cluster_vectors import choose_k_by_silhouette, cluster_kmeans
from .embed_texts import build_corpus_for_articles, embed_texts, store_embeddings
from .store import load_store, save_store


def run_embedding_and_clustering(
    source_field: str,
    embedding_field: str,
    cluster_field: str,
    model_name: str = "all-MiniLM-L6-v2",
    k: Optional[int] = None,
    fallback_fields: Optional[list[str]] = None,
    batch_size: int = 32,
    normalize: bool = True,
) -> dict:
    """
    Embed one canonical text field and cluster it.
    Example source_field: 'summary_ollama', 'summary_haiku', or 'fulltext'.
    """
    store = load_store()

    article_ids, texts = build_corpus_for_articles(
        store,
        field=source_field,
        fallback_fields=fallback_fields,
    )
    if not texts:
        raise ValueError(f"No texts available for field '{source_field}'.")

    vectors = embed_texts(
        texts,
        model_name=model_name,
        batch_size=batch_size,
        normalize=normalize,
    )
    store_embeddings(store, article_ids, vectors, embedding_field)

    if k is None:
        scores = choose_k_by_silhouette(vectors)
        if not scores:
            raise ValueError(
                "Unable to choose k automatically. Provide k explicitly or use a larger corpus."
            )
        k = max(scores, key=scores.get)

    labels = cluster_kmeans(vectors, n_clusters=k)

    for article_id, label in zip(article_ids, labels):
        article = store[article_id]
        setattr(article, cluster_field, int(label))

    save_store(store)
    return {
        "source_field": source_field,
        "embedding_field": embedding_field,
        "cluster_field": cluster_field,
        "model_name": model_name,
        "k": k,
        "n_articles": len(article_ids),
        "embedding_dim": int(vectors.shape[1]) if vectors.ndim == 2 else 0,
    }