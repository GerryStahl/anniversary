from typing import Optional

from .models import Article
from .store import load_store, save_store
from .llm import ollama_chat


CATEGORY_SYSTEM_PROMPT = """
You classify IJCSCL articles into exactly one category.

Return only one letter:
a. design of collaboration
b. design of technology to support learning
c. analysis of interaction among students
d. measurement of learning
e. editorial (filename ending in 0)
f. none of the above

Choose the best primary category. Return only the single letter.
""".strip()


def build_category_prompt(article: Article) -> str:
    """
    Construct the user prompt from title and summary.
    """
    title = article.title or ""
    summary = article.summary_ollama or ""
    filename = article.filename or ""
    return f"""
Filename: {filename}
Title: {title}
Summary: {summary}
""".strip()


def normalize_category(text: str) -> str:
    """
    Keep only a valid single-letter category.
    """
    cleaned = text.strip().lower()
    for ch in cleaned:
        if ch in {"a", "b", "c", "d", "e", "f"}:
            return ch
    return "f"


def classify_article(
    article: Article,
    model: str = "llama3.3:8b",
    host: Optional[str] = None,
    temperature: float = 0.0,
) -> str:
    """
    Classify a single article and return a category letter.
    """
    user_prompt = build_category_prompt(article)
    result = ollama_chat(
        model=model,
        system_prompt=CATEGORY_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        host=host,
        temperature=temperature,
    )
    return normalize_category(result)


def classify_store(
    model: str = "llama3.3:8b",
    host: Optional[str] = None,
    overwrite: bool = False,
) -> None:
    """
    Classify all articles in the store and save the updated PKL/JSON.
    """
    store = load_store()

    for article_id, article in store.items():
        if article.category and not overwrite:
            continue
        if not article.summary_ollama and not article.fulltext:
            continue

        category = classify_article(article, model=model, host=host)
        article.category = category

    save_store(store)


def classify_one(
    article_id: str,
    model: str = "llama3.3:8b",
    host: Optional[str] = None,
) -> str:
    """
    Classify a single article by id and persist the result.
    """
    store = load_store()
    article = store[article_id]
    category = classify_article(article, model=model, host=host)
    article.category = category
    save_store(store)
    return category
