import csv
import sys
from collections import Counter

sys.path.insert(0, ".")
import src.store as s

KEYWORDS = [
    "interaction analysis",
    "discourse analysis",
    "conversation analysis",
    "dialogic",
    "transactivity",
    "sequential analysis",
    "process mining",
    "network analysis",
    "epistemic network analysis",
    "multimodal",
    "gesture",
    "orchestration",
    "group awareness",
    "dashboard",
    "real-time",
    "synchronous",
    "asynchronous",
    "wiki",
    "chat",
    "forum",
    "collaborative interaction",
    "meaning-making",
    "uptake",
    "participation",
    "peer talk",
]

store = s.load_store()
rows = []
for article in store.values():
    if not isinstance(article.year, int) or not (2006 <= article.year <= 2025):
        continue
    if article.editorial == "editorial" or article.article_number == 0:
        continue
    blob = " ".join(
        [
            article.title or "",
            article.summary_haiku or "",
            article.methodology_primary or "",
            " ".join(article.methodology_secondary or []),
            article.unit_of_analysis_primary or "",
            " ".join(article.unit_of_analysis_secondary or []),
            article.technology_primary or "",
            " ".join(article.technology_secondary or []),
            article.theory_primary or "",
            " ".join(article.theory_secondary or []),
        ]
    ).lower()
    score = sum(blob.count(term) for term in KEYWORDS)
    rows.append(
        {
            "score": score,
            "id": article.id,
            "year": article.year,
            "title": article.title or "",
            "authors": ", ".join(article.authors) if isinstance(article.authors, list) else (article.authors or ""),
            "doi": article.doi or "",
            "methodology_primary": article.methodology_primary or "",
            "methodology_secondary": " | ".join(article.methodology_secondary or []),
            "unit_of_analysis_primary": article.unit_of_analysis_primary or "",
            "unit_of_analysis_secondary": " | ".join(article.unit_of_analysis_secondary or []),
            "technology_primary": article.technology_primary or "",
            "technology_secondary": " | ".join(article.technology_secondary or []),
            "theory_primary": article.theory_primary or "",
            "theory_secondary": " | ".join(article.theory_secondary or []),
            "summary_haiku": (article.summary_haiku or "").replace("\n", " "),
        }
    )

rows.sort(key=lambda row: (-row["score"], row["year"], row["id"]))

out_path = "reports/_2006_2025_interaction_analysis_review.csv"
with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "score",
            "id",
            "year",
            "title",
            "authors",
            "doi",
            "methodology_primary",
            "methodology_secondary",
            "unit_of_analysis_primary",
            "unit_of_analysis_secondary",
            "technology_primary",
            "technology_secondary",
            "theory_primary",
            "theory_secondary",
            "summary_haiku",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"wrote {out_path} with {len(rows)} rows")
print("top methodologies:")
method_counts = Counter(r["methodology_primary"] for r in rows)
for name, count in method_counts.most_common(12):
    print(f"{name}\t{count}")
print("top scored candidates:")
for row in rows[:40]:
    print(f"{row['score']}\t{row['year']}\t{row['id']}\t{row['title']}\t{row['methodology_primary']}")
