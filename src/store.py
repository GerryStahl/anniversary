import json
import pickle
from typing import Dict

from .config import PKL_PATH, JSON_PATH, PROCESSED_DIR
from .models import Article


ArticlesStore = Dict[str, Article]  # key: article.id


def load_store() -> ArticlesStore:
    """
    Load the current article store from PKL if it exists, else return empty dict.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if PKL_PATH.exists():
        with PKL_PATH.open("rb") as f:
            store: ArticlesStore = pickle.load(f)
        # Migrate articles pickled before canonical field names were introduced.
        # Use __dict__ directly to bypass dataclass class-level default lookup.
        for article in store.values():
            if "fulltext" not in article.__dict__:
                article.fulltext = article.__dict__.get("text", None)

            if "summary_ollama" not in article.__dict__:
                article.summary_ollama = article.__dict__.get(
                    "ollama_summary",
                    article.__dict__.get("summary", None),
                )

            if "summary_haiku" not in article.__dict__:
                article.summary_haiku = article.__dict__.get("claude_summary", None)

            if "embedding_ollama_summary" not in article.__dict__:
                article.embedding_ollama_summary = None
            if "embedding_haiku_summary" not in article.__dict__:
                article.embedding_haiku_summary = None
            if "embedding_fulltext" not in article.__dict__:
                article.embedding_fulltext = article.__dict__.get("embedding", None)

            if "cluster_ollama_summary" not in article.__dict__:
                article.cluster_ollama_summary = None
            if "cluster_haiku_summary" not in article.__dict__:
                article.cluster_haiku_summary = None
            if "cluster_fulltext" not in article.__dict__:
                article.cluster_fulltext = None

            if "methodology_primary" not in article.__dict__:
                article.methodology_primary = None
            if "methodology_secondary" not in article.__dict__:
                article.methodology_secondary = None
            if "unit_of_analysis_primary" not in article.__dict__:
                article.unit_of_analysis_primary = None
            if "unit_of_analysis_secondary" not in article.__dict__:
                article.unit_of_analysis_secondary = None
            if "pedagogy_primary" not in article.__dict__:
                article.pedagogy_primary = None
            if "pedagogy_secondary" not in article.__dict__:
                article.pedagogy_secondary = None
            if "technology_primary" not in article.__dict__:
                article.technology_primary = None
            if "technology_secondary" not in article.__dict__:
                article.technology_secondary = None
            if "theory_primary" not in article.__dict__:
                article.theory_primary = None
            if "theory_secondary" not in article.__dict__:
                article.theory_secondary = None
            if "ai_llm_involvement_primary" not in article.__dict__:
                article.ai_llm_involvement_primary = None
            if "ai_llm_involvement_secondary" not in article.__dict__:
                article.ai_llm_involvement_secondary = None

            if "evidence_span" not in article.__dict__:
                article.evidence_span = None
            if "coding_confidence" not in article.__dict__:
                article.coding_confidence = None
            if "extends_methodology" not in article.__dict__:
                article.extends_methodology = None
            if "extends_pedagogy" not in article.__dict__:
                article.extends_pedagogy = None
            if "extends_technology" not in article.__dict__:
                article.extends_technology = None
            if "extends_theory" not in article.__dict__:
                article.extends_theory = None
            if "coding_notes" not in article.__dict__:
                article.coding_notes = None
        return store
    return {}


def save_store(store: ArticlesStore) -> None:
    """
    Save the canonical PKL and a human-readable JSON mirror (without full text).
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # PKL
    with PKL_PATH.open("wb") as f:
        pickle.dump(store, f)

    # JSON mirror
    jsonable = {
        article_id: article.to_dict(include_text=False, include_embeddings=False)
        for article_id, article in store.items()
    }
    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(jsonable, f, indent=2, ensure_ascii=False)


def upsert_article(store: ArticlesStore, article: Article) -> None:
    """
    Insert or update an article by id.
    """
    store[article.id] = article


def get_article(store: ArticlesStore, article_id: str) -> Article:
    return store[article_id]


def update_article(store: ArticlesStore, article_id: str, **fields) -> None:
    """
    Update fields of an existing article in place.
    """
    article = store[article_id]
    for k, v in fields.items():
        setattr(article, k, v)
