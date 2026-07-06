import csv
from pathlib import Path

from src.categorize import classify_store
from src.store import load_store


def authors_to_str(authors):
    if authors is None:
        return ""
    if isinstance(authors, list):
        return " & ".join(str(x) for x in authors)
    return str(authors)


def main():
    classify_store(model="llama3.1:8b", overwrite=False)

    store = load_store()
    articles = list(store.values())
    articles.sort(
        key=lambda a: (
            a.volume if a.volume is not None else 9999,
            a.issue if a.issue is not None else 9999,
            a.article_number if a.article_number is not None else 9999,
            a.id,
        )
    )

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "articles.csv"

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "volume",
            "issue",
            "article_number",
            "title",
            "authors",
            "category",
            "summary_ollama",
            "summary_haiku",
        ])
        for a in articles:
            writer.writerow([
                a.volume if a.volume is not None else "",
                a.issue if a.issue is not None else "",
                a.article_number if a.article_number is not None else "",
                a.title or "",
                authors_to_str(a.authors),
                a.category or "",
                a.summary_ollama or "",
                a.summary_haiku or "",
            ])

    categorized = sum(1 for a in articles if a.category)
    print("TOTAL_ARTICLES", len(articles))
    print("CATEGORIZED", categorized)
    print("CSV_PATH", out_path)

    for target in ["ijCSCL_4_1_2", "ijCSCL_10_1_0", "ijCSCL_1_1_0"]:
        a = store.get(target)
        if a:
            print("CHECK", target, "category=", a.category)


if __name__ == "__main__":
    main()
