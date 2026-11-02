#!/usr/bin/env python3

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

from src.store import load_store
from src.trend_filters import is_excluded_article_record


DIMENSIONS = [
    "methodology_primary",
    "unit_of_analysis_primary",
    "pedagogy_primary",
    "technology_primary",
    "theory_primary",
    "ai_llm_involvement_primary",
]

OUTPUT_DIR = Path("reports/dimension_primary_trends")
START_YEAR = 2006
END_YEAR = 2025


def build_counts(store):
    years = list(range(START_YEAR, END_YEAR + 1))
    counts = {dim: defaultdict(lambda: defaultdict(int)) for dim in DIMENSIONS}
    values_by_dim = {dim: set() for dim in DIMENSIONS}

    for article in store.values():
        if (
            is_excluded_article_record(article)
            or not isinstance(article.year, int)
            or not START_YEAR <= article.year <= END_YEAR
        ):
            continue
        year = article.year
        for dim in DIMENSIONS:
            value = getattr(article, dim, None)
            if not value:
                continue
            value = str(value).strip()
            if not value:
                continue
            counts[dim][year][value] += 1
            values_by_dim[dim].add(value)

    return years, counts, values_by_dim


def slug(name: str) -> str:
    return name.replace("_primary", "")


def write_csv(path: Path, years: list[int], dim_counts, values: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["year"] + values
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for year in years:
            row = {"year": year}
            for value in values:
                row[value] = dim_counts[year].get(value, 0)
            writer.writerow(row)


def write_chart(path: Path, years: list[int], dim: str, dim_counts, values: list[str]) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(13, 7))

    for value in values:
        y = [dim_counts[year].get(value, 0) for year in years]
        ax.plot(years, y, marker="o", linewidth=1.8, label=value)

    ax.set_title(f"{dim} by year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Article count")
    ax.set_xticks(years)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(title=dim, loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=8)
    fig.tight_layout()

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    store = load_store()
    years, counts, values_by_dim = build_counts(store)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for dim in DIMENSIONS:
        values = sorted(values_by_dim[dim])
        dim_slug = slug(dim)
        csv_path = OUTPUT_DIR / f"{dim_slug}_year_counts.csv"
        png_path = OUTPUT_DIR / f"{dim_slug}_year_trend.png"

        write_csv(csv_path, years, counts[dim], values)
        write_chart(png_path, years, dim, counts[dim], values)

        print(f"CSV {csv_path}")
        print(f"PNG {png_path}")

    print(f"YEARS {START_YEAR}-{END_YEAR}")


if __name__ == "__main__":
    main()
