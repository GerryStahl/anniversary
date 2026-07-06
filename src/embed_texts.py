from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from .store import ArticlesStore, load_store, save_store


def build_corpus_for_articles(
    store: ArticlesStore,
    field: str,
    fallback_fields: Optional[list[str]] = None,
) -> tuple[list[str], list[str]]:
    """
    Return (article_ids, texts) for embedding from one canonical article field.
    Supported primary fields include 'summary_ollama', 'summary_haiku', and 'fulltext'.
    """
    article_ids: list[str] = []
    texts: list[str] = []

    for article_id, article in store.items():
        text = getattr(article, field, None)

        if not text and fallback_fields:
            for fallback_field in fallback_fields:
                text = getattr(article, fallback_field, None)
                if text:
                    break

        if not text:
            continue

        cleaned = str(text).strip()
        if not cleaned:
            continue

        article_ids.append(article_id)
        texts.append(cleaned)

    return article_ids, texts


def embed_texts(
    texts: list[str],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 32,
    normalize: bool = True,
) -> np.ndarray:
    """
    Embed a list of texts into a dense vector space.
    """
    if not texts:
        raise ValueError("No texts were provided for embedding.")

    model = SentenceTransformer(model_name)
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
        show_progress_bar=True,
    )
    return np.asarray(vectors, dtype=float)


def store_embeddings(
    store: ArticlesStore,
    article_ids: list[str],
    vectors: np.ndarray,
    embedding_field: str,
) -> None:
    """
    Store vectors on each article record.
    """
    if len(article_ids) != len(vectors):
        raise ValueError("article_ids and vectors must be the same length.")

    for article_id, vector in zip(article_ids, vectors):
        article = store[article_id]
        setattr(article, embedding_field, np.asarray(vector, dtype=float).tolist())


def embed_corpus_field(
    field: str,
    embedding_field: str,
    model_name: str = "all-MiniLM-L6-v2",
    fallback_fields: Optional[list[str]] = None,
    batch_size: int = 32,
    normalize: bool = True,
) -> dict:
    """
    Embed all texts from one article field and persist the vectors.
    """
    store = load_store()
    article_ids, texts = build_corpus_for_articles(
        store,
        field=field,
        fallback_fields=fallback_fields,
    )
    if not texts:
        raise ValueError(f"No texts available for field '{field}'.")

    vectors = embed_texts(
        texts,
        model_name=model_name,
        batch_size=batch_size,
        normalize=normalize,
    )
    store_embeddings(store, article_ids, vectors, embedding_field)
    save_store(store)
    return {
        "field": field,
        "embedding_field": embedding_field,
        "model_name": model_name,
        "n_articles": len(article_ids),
        "embedding_dim": int(vectors.shape[1]) if vectors.ndim == 2 else 0,
    }