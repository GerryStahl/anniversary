import csv
import re
import unicodedata
from pathlib import Path

from src.store import load_store

CORRECTIONS_PATH = Path("data/metadata_corrections.csv")

FIELDS = [
    "id",
    "title",
    "authors",
    "editorial",
    "doi",
    "year",
    "volume",
    "issue",
    "article_number",
    "notes",
]


def to_ascii_name_text(text: str) -> str:
    if not isinstance(text, str):
        return text

    # Normalize compatibility and punctuation variants
    t = unicodedata.normalize("NFKC", text)
    t = (
        t.replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("‐", "-")
        .replace("‑", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("·", " & ")
    )

    # Strip diacritics only
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))

    # Cleanup spacing around separators
    t = re.sub(r"\s*&\s*", " & ", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t


def load_corrections(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save_corrections(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def upsert_authors(rows, article_id: str, authors: str, note_suffix: str):
    for row in rows:
        if row.get("id") == article_id:
            row["authors"] = authors
            notes = (row.get("notes") or "").strip()
            if note_suffix not in notes:
                row["notes"] = (notes + " | " + note_suffix).strip(" |")
            return

    rows.append(
        {
            "id": article_id,
            "title": "",
            "authors": authors,
            "editorial": "",
            "doi": "",
            "year": "",
            "volume": "",
            "issue": "",
            "article_number": "",
            "notes": note_suffix,
        }
    )


def main():
    store = load_store()
    corr_rows = load_corrections(CORRECTIONS_PATH)

    changed = []
    for article in store.values():
        current = article.authors
        if isinstance(current, list):
            current_text = " & ".join(str(x).strip() for x in current if str(x).strip())
        elif isinstance(current, str):
            current_text = current.strip()
        else:
            continue

        if not current_text:
            continue

        ascii_text = to_ascii_name_text(current_text)
        if ascii_text and ascii_text != current_text:
            upsert_authors(
                corr_rows,
                article.id,
                ascii_text,
                "Automated author cleanup (special-character normalization)",
            )
            changed.append((article.id, current_text, ascii_text))

    if changed:
        save_corrections(CORRECTIONS_PATH, corr_rows)

    print("AUTHOR_SPECIAL_CHAR_CHANGES", len(changed))
    for article_id, old, new in changed[:80]:
        print("---", article_id)
        print("OLD:", old)
        print("NEW:", new)


if __name__ == "__main__":
    main()
