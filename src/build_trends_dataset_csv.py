import argparse
import csv
from pathlib import Path

from src.store import load_store


def editor_era_for_year(year: int | None) -> str:
    if year is None:
        return "unknown"
    if 2006 <= year <= 2015:
        return "stahl_hesse_2006_2015"
    if 2016 <= year <= 2019:
        return "ludvigsen_2016_2019"
    if 2020 <= year <= 2023:
        return "rose_jarvela_2020_2023"
    if 2024 <= year <= 2027:
        return "baker_reimann_2024_2027"
    return "outside_configured_era"


def list_to_pipe(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "|".join(str(v) for v in value)
    return str(value)


def is_editorial(article) -> bool:
    return article.editorial == "editorial" or article.article_number == 0


def build_trends_dataset(output_path: Path, include_editorials: bool = False) -> tuple[int, int]:
    store = load_store()
    articles = list(store.values())
    articles.sort(
        key=lambda a: (
            a.year if a.year is not None else 9999,
            a.volume if a.volume is not None else 9999,
            a.issue if a.issue is not None else 9999,
            a.article_number if a.article_number is not None else 9999,
            a.id,
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    excluded_editorials = 0
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "id",
                "year",
                "volume",
                "issue",
                "article_number",
                "editor_era",
                "is_editorial",
                "title",
                "authors",
                "category",
                "cluster_haiku_summary",
                "summary_haiku",
                "methodology_primary",
                "methodology_secondary",
                "unit_of_analysis_primary",
                "unit_of_analysis_secondary",
                "pedagogy_primary",
                "pedagogy_secondary",
                "technology_primary",
                "technology_secondary",
                "theory_primary",
                "theory_secondary",
                "ai_llm_involvement_primary",
                "ai_llm_involvement_secondary",
                "evidence_span",
                "coding_confidence",
                "extends_methodology",
                "extends_pedagogy",
                "extends_technology",
                "extends_theory",
                "coding_notes",
            ]
        )

        for article in articles:
            article_is_editorial = is_editorial(article)
            if article_is_editorial and not include_editorials:
                excluded_editorials += 1
                continue

            writer.writerow(
                [
                    article.id,
                    article.year if article.year is not None else "",
                    article.volume if article.volume is not None else "",
                    article.issue if article.issue is not None else "",
                    article.article_number if article.article_number is not None else "",
                    editor_era_for_year(article.year),
                    "yes" if article_is_editorial else "no",
                    article.title or "",
                    list_to_pipe(article.authors),
                    article.category or "",
                    article.cluster_haiku_summary if article.cluster_haiku_summary is not None else "",
                    article.summary_haiku or "",
                    article.methodology_primary or "",
                    list_to_pipe(article.methodology_secondary),
                    article.unit_of_analysis_primary or "",
                    list_to_pipe(article.unit_of_analysis_secondary),
                    article.pedagogy_primary or "",
                    list_to_pipe(article.pedagogy_secondary),
                    article.technology_primary or "",
                    list_to_pipe(article.technology_secondary),
                    article.theory_primary or "",
                    list_to_pipe(article.theory_secondary),
                    article.ai_llm_involvement_primary or "",
                    list_to_pipe(article.ai_llm_involvement_secondary),
                    article.evidence_span or "",
                    article.coding_confidence if article.coding_confidence is not None else "",
                    article.extends_methodology if article.extends_methodology is not None else "",
                    article.extends_pedagogy if article.extends_pedagogy is not None else "",
                    article.extends_technology if article.extends_technology is not None else "",
                    article.extends_theory if article.extends_theory is not None else "",
                    article.coding_notes or "",
                ]
            )
            written += 1

    return written, excluded_editorials


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build analysis-ready trends dataset from PKL store with editorials excluded by default."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/trends_dataset.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--include-editorials",
        action="store_true",
        help="Include editorials in the output file",
    )
    args = parser.parse_args()

    rows_written, editorials_excluded = build_trends_dataset(
        Path(args.output), include_editorials=args.include_editorials
    )
    print("CSV_PATH", args.output)
    print("ROWS_WRITTEN", rows_written)
    print("EDITORIALS_EXCLUDED", editorials_excluded)


if __name__ == "__main__":
    main()
