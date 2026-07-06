from typing import Optional

from .models import Article
from .store import load_store, save_store
from .llm import ollama_chat


SUMMARIZATION_SYSTEM_PROMPT = """
You are an expert in computer-supported collaborative learning.
Write a concise 50-60 word summary of the article's central claim or finding.
Focus on the main research question, method type, and conclusion.
Do not mention that you are summarizing.
Return only the summary text.
""".strip()


def build_summarization_prompt(article: Article) -> str:
    """
    Construct the user prompt from article metadata and text.
    """
    header = f"""
Title: {article.title or ""}
Authors: {", ".join(article.authors or [])}
Year: {article.year or ""}
Volume: {article.volume or ""}
Issue: {article.issue or ""}
Article ID: {article.id}
""".strip()

    body = article.fulltext or ""
    return f"{header}\n\nArticle text:\n{body}"


def clean_summary(text: str) -> str:
    """
    Normalize whitespace and trim to a single paragraph.
    """
    return " ".join(text.split()).strip()


def word_count(text: str) -> int:
    return len(clean_summary(text).split())


def summarize_article(
    article: Article,
    model: str = "llama3.3:8b",
    host: Optional[str] = None,
    temperature: float = 0.2,
) -> str:
    """
    Generate and return a summary for one article.
    """
    user_prompt = build_summarization_prompt(article)
    summary = ollama_chat(
        model=model,
        system_prompt=SUMMARIZATION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        host=host,
        temperature=temperature,
    )
    return clean_summary(summary)


def summarize_store(
    model: str = "llama3.3:8b",
    host: Optional[str] = None,
    overwrite: bool = False,
) -> None:
    """
    Summarize all articles in the store and save the updated PKL/JSON.
    """
    store = load_store()

    for article_id, article in store.items():
        if article.summary_ollama and not overwrite:
            continue
        if not article.fulltext:
            continue

        summary = summarize_article(article, model=model, host=host)
        article.summary_ollama = summary

    save_store(store)


def summarize_one(
    article_id: str,
    model: str = "llama3.3:8b",
    host: Optional[str] = None,
) -> str:
    """
    Summarize a single article by id and persist the result.
    """
    store = load_store()
    article = store[article_id]
    summary = summarize_article(article, model=model, host=host)
    article.summary_ollama = summary
    save_store(store)
    return summary
