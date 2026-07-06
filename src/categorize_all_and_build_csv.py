from pathlib import Path

from src.categorize import classify_store
from src.build_articles_csv import build_articles_csv
from src.store import load_store


def main():
    classify_store(model="llama3.1:8b", overwrite=False)
    out_path = build_articles_csv(Path("reports/articles.csv"))

    store = load_store()
    articles = list(store.values())

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
