import argparse
import csv
from pathlib import Path

from src.store import load_store


def norm(text: str) -> str:
    return " ".join((text or "").lower().split())


def make_manifest_id(row: dict) -> str:
    doi = (row.get("doi") or "").strip()
    if doi:
        return f"manifest:{doi}"
    year = (row.get("year") or "").strip()
    vol = (row.get("volume") or "").strip()
    iss = (row.get("issue") or "").strip()
    title = norm(row.get("title") or "")[:80]
    return f"manifest:{year}:v{vol}:i{iss}:{title}"


def build_all_articles_index(output_path: Path) -> tuple[int, int, int]:
    store = load_store()

    rows = []
    seen_ids = set()
    seen_title_keys = set()

    # 1) Add all existing store articles
    for article_id, article in store.items():
        seen_ids.add(article_id)
        title_key = norm(article.title or "")
        if title_key:
            seen_title_keys.add(title_key)

        rows.append(
            {
                "id": article_id,
                "authors": article.authors or "",
                "editorial": article.editorial or "",
                "title": article.title or "",
            }
        )

    # 2) Add manifest-only articles (not yet downloaded / not in store)
    manifest_path = Path("data/raw 2016-2026/metadata/manifest_oa_2016_present.csv")
    manifest_added = 0

    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = (row.get("title") or "").strip()
                title_key = norm(title)

                # Skip if likely already represented in store
                if title_key and title_key in seen_title_keys:
                    continue

                item_id = make_manifest_id(row)
                if item_id in seen_ids:
                    continue

                rows.append(
                    {
                        "id": item_id,
                        "authors": "",
                        "editorial": "",
                        "title": title,
                    }
                )
                seen_ids.add(item_id)
                if title_key:
                    seen_title_keys.add(title_key)
                manifest_added += 1

    # Stable sort by title then id
    rows.sort(key=lambda r: (norm(r["title"]), r["id"]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "authors", "editorial", "title"])
        writer.writeheader()
        writer.writerows(rows)

    return len(store), manifest_added, len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a combined article index CSV (store + manifest-only articles)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/all_articles_id_authors_editorial_title.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    output = Path(args.output)
    store_count, manifest_added, total_rows = build_all_articles_index(output)
    print("CSV_PATH", output)
    print("STORE_ARTICLES", store_count)
    print("MANIFEST_ONLY_ADDED", manifest_added)
    print("TOTAL_ROWS", total_rows)


if __name__ == "__main__":
    main()
