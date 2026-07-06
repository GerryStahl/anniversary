#!/usr/bin/env python3
"""Create a volume/category spreadsheet and a category count chart from articles.csv."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

DEFAULT_INPUT = Path("reports/articles.csv")
DEFAULT_OUTPUT_CSV = Path("reports/categories.csv")
DEFAULT_OUTPUT_PNG = Path("reports/volume_category_counts.png")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate categories.csv and a volume-by-category line chart from articles.csv."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help=f"Source CSV path (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output-csv",
        default=str(DEFAULT_OUTPUT_CSV),
        help=f"Output CSV path with volume/category columns (default: {DEFAULT_OUTPUT_CSV})",
    )
    parser.add_argument(
        "--output-png",
        default=str(DEFAULT_OUTPUT_PNG),
        help=f"Output chart path (default: {DEFAULT_OUTPUT_PNG})",
    )
    return parser.parse_args()


def read_articles(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_categories_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["volume", "category"])
        writer.writeheader()
        for row in rows:
            writer.writerow({"volume": row["volume"], "category": row["category"]})


def build_category_counts(rows: list[dict[str, str]]) -> tuple[list[int], dict[str, list[int]]]:
    volumes = sorted({int(row["volume"]) for row in rows})
    categories = sorted({row["category"].strip() for row in rows if row["category"].strip()})

    counts_by_volume_and_category: dict[int, Counter[str]] = defaultdict(Counter)
    for row in rows:
        volume = int(row["volume"])
        category = row["category"].strip()
        if category:
            counts_by_volume_and_category[volume][category] += 1

    series: dict[str, list[int]] = {}
    for category in categories:
        series[category] = [counts_by_volume_and_category[volume][category] for volume in volumes]

    return volumes, series


def save_chart(volumes: list[int], series: dict[str, list[int]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(12, 7))
    color_map = mpl.colormaps["tab10"]

    category_labels = {
        "a": "a: collaboration design",
        "b": "b: technology for learning",
        "c": "c: interaction analysis",
        "d": "d: learning measurement",
        "e": "e: editorial",
        "f": "f: other",
    }

    for index, (category, counts) in enumerate(sorted(series.items())):
        ax.plot(
            volumes,
            counts,
            marker="o",
            linewidth=2,
            color=color_map(index),
            label=category_labels.get(category, category),
        )

    ax.set_xlabel("Volume")
    ax.set_ylabel("Number of articles")
    ax.set_title("Category counts by volume")
    ax.set_xticks(volumes)
    ax.legend(title="Category", loc="upper left", bbox_to_anchor=(1.02, 1))
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_csv = Path(args.output_csv)
    output_png = Path(args.output_png)

    rows = read_articles(input_path)
    write_categories_csv(rows, output_csv)
    volumes, series = build_category_counts(rows)
    save_chart(volumes, series, output_png)

    print(f"Wrote {output_csv}")
    print(f"Wrote {output_png}")
    print(f"Volumes covered: {len(volumes)}")
    print(f"Categories covered: {', '.join(sorted(series.keys()))}")


if __name__ == "__main__":
    main()
