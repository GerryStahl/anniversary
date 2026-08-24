import csv
from pathlib import Path

from src.store import load_store


OUT_CSV = Path("reports/test_articles_non_null_category_coding.csv")


def _authors_to_text(authors) -> str:
    if isinstance(authors, list):
        return " | ".join(str(a).strip() for a in authors if str(a).strip())
    return str(authors or "")


def main() -> None:
    store = load_store()

    rows = []
    for article in store.values():
        if article.category is None:
            continue
        if isinstance(article.category, str) and not article.category.strip():
            continue

        rows.append(
            {
                "year": article.year,
                "volume": article.volume,
                "issue": article.issue,
                "article": article.article_number,
                "editorial": article.editorial,
                "authors": _authors_to_text(article.authors),
                "title": article.title,
                "category": article.category,
                "methodology_primary": article.methodology_primary,
                "unit_of_analysis_primary": article.unit_of_analysis_primary,
                "pedagogy_primary": article.pedagogy_primary,
                "technology_primary": article.technology_primary,
                "theory_primary": article.theory_primary,
                "ai_llm_involvement_primary": article.ai_llm_involvement_primary,
                "summary_haiku": article.summary_haiku,
            }
        )

    rows.sort(
        key=lambda r: (
            r["year"] if isinstance(r["year"], int) else 9999,
            r["volume"] if isinstance(r["volume"], int) else 999,
            r["issue"] if isinstance(r["issue"], int) else 999,
            r["article"] if isinstance(r["article"], int) else 999,
            str(r["title"] or ""),
        )
    )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "year",
        "volume",
        "issue",
        "article",
        "editorial",
        "authors",
        "title",
        "category",
        "methodology_primary",
        "unit_of_analysis_primary",
        "pedagogy_primary",
        "technology_primary",
        "theory_primary",
        "ai_llm_involvement_primary",
        "summary_haiku",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"WROTE {OUT_CSV} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
