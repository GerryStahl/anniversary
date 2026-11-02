#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

from src.store import load_store
from src.trend_filters import is_excluded_article_record


DEFAULT_OUTPUT_CSV = Path("reports/year_cluster_counts_2006_2025.csv")
DEFAULT_OUTPUT_PNG = Path("reports/year_cluster_counts_2006_2025.png")
START_YEAR = 2006
END_YEAR = 2025


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate year-by-cluster counts and a multi-line trend chart using cluster_haiku_summary."
    )
    parser.add_argument(
        "--output-csv",
        default=str(DEFAULT_OUTPUT_CSV),
        help=f"Output CSV path (default: {DEFAULT_OUTPUT_CSV})",
    )
    parser.add_argument(
        "--output-png",
        default=str(DEFAULT_OUTPUT_PNG),
        help=f"Output chart path (default: {DEFAULT_OUTPUT_PNG})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_csv = Path(args.output_csv)
    output_png = Path(args.output_png)

    store = load_store()
    years = list(range(START_YEAR, END_YEAR + 1))
    counts_by_year_cluster: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    clusters = set()

    for article in store.values():
        if is_excluded_article_record(article):
            continue
        year = article.year
        if not isinstance(year, int):
            continue
        if year < START_YEAR or year > END_YEAR:
            continue

        cluster = article.cluster_haiku_summary
        if cluster is None:
            continue

        counts_by_year_cluster[year][int(cluster)] += 1
        clusters.add(int(cluster))

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["year"] + [str(c) for c in sorted(clusters)]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for year in years:
            row = {"year": year}
            for cluster in sorted(clusters):
                row[str(cluster)] = counts_by_year_cluster[year].get(cluster, 0)
            writer.writerow(row)

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(12, 7))

    for cluster in sorted(clusters):
        y_values = [counts_by_year_cluster[year].get(cluster, 0) for year in years]
        ax.plot(
            years,
            y_values,
            marker="o",
            linewidth=2,
            label=f"cluster {cluster}",
        )

    ax.set_title("Haiku Cluster Count by Year (2006-2025)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Articles")
    ax.set_xticks(years)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(title="Cluster", loc="upper left", bbox_to_anchor=(1.02, 1))
    fig.tight_layout()

    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"CSV {output_csv}")
    print(f"PNG {output_png}")
    print(f"YEARS {START_YEAR}-{END_YEAR}")
    print(f"CLUSTERS {sorted(clusters)}")


if __name__ == "__main__":
    main()
