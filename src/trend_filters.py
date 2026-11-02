from __future__ import annotations


NON_ARTICLE_CATEGORIES = {"e", "f"}


def is_editorial_record(article) -> bool:
    editorial = (getattr(article, "editorial", None) or "").strip().lower()
    return editorial == "editorial" or getattr(article, "article_number", None) == 0


def is_excluded_article_record(article) -> bool:
    editorial = (getattr(article, "editorial", None) or "").strip()
    category = (getattr(article, "category", None) or "").strip().lower()
    return bool(editorial) or getattr(article, "article_number", None) == 0 or category in NON_ARTICLE_CATEGORIES


def is_excluded_trend_row(row: dict[str, str]) -> bool:
    editorial = (row.get("editorial") or "").strip()
    category = (row.get("category") or "").strip().lower()
    article_number = (row.get("article_number") or "").strip()
    return (
        bool(editorial)
        or row.get("is_editorial", "").strip().lower() == "yes"
        or article_number == "0"
        or category in NON_ARTICLE_CATEGORIES
    )
