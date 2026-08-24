#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from scipy import stats

DEFAULT_INPUT = Path("reports/trends_dataset.csv")
DEFAULT_OUTPUT = Path("reports/trend_significance_tests.csv")
DEFAULT_SUMMARY = Path("reports/trend_significance_summary.csv")

SERIES_FIELDS = [
    "category",
    "cluster_haiku_summary",
    "methodology_primary",
    "unit_of_analysis_primary",
    "pedagogy_primary",
    "technology_primary",
    "theory_primary",
    "ai_llm_involvement_primary",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run statistical significance tests for yearly trend lines by category/cluster/dimensions."
    )
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Input trends dataset CSV")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output long-form test results CSV")
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY), help="Output compact significant-only CSV")
    parser.add_argument("--year-start", type=int, default=None, help="Optional lower year bound")
    parser.add_argument("--year-end", type=int, default=None, help="Optional upper year bound")
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_int(value: str) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def bh_fdr(pvals: list[float]) -> list[float]:
    n = len(pvals)
    if n == 0:
        return []
    order = sorted(range(n), key=lambda i: pvals[i])
    ranked = [pvals[i] for i in order]

    q = [0.0] * n
    prev = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        val = ranked[i] * n / rank
        prev = min(prev, val)
        q[i] = min(prev, 1.0)

    out = [0.0] * n
    for idx, original_idx in enumerate(order):
        out[original_idx] = q[idx]
    return out


def main() -> None:
    args = parse_args()
    rows = read_rows(Path(args.input))

    filtered = []
    for r in rows:
        y = to_int(r.get("year", ""))
        if y is None:
            continue
        if args.year_start is not None and y < args.year_start:
            continue
        if args.year_end is not None and y > args.year_end:
            continue
        filtered.append(r)

    if not filtered:
        raise SystemExit("No rows after filtering")

    years = sorted({to_int(r["year"]) for r in filtered if to_int(r["year"]) is not None})
    year_index = {y: i for i, y in enumerate(years)}

    counts_by_field_value_year: dict[str, dict[str, Counter[int]]] = defaultdict(
        lambda: defaultdict(Counter)
    )

    for r in filtered:
        y = to_int(r["year"])
        if y is None:
            continue
        for field in SERIES_FIELDS:
            val = (r.get(field) or "").strip()
            if not val:
                continue
            counts_by_field_value_year[field][val][y] += 1

    results: list[dict[str, str | float | int]] = []
    pvals_for_fdr: list[float] = []
    pvals_row_idx: list[int] = []

    x = list(range(len(years)))

    for field, by_val in counts_by_field_value_year.items():
        for val, year_counts in by_val.items():
            y_counts = [year_counts.get(year, 0) for year in years]

            total = sum(y_counts)
            n_nonzero = sum(1 for c in y_counts if c > 0)
            if len(set(y_counts)) <= 1:
                # flat line; keep a row with NA-like metrics
                results.append(
                    {
                        "field": field,
                        "value": val,
                        "n_years": len(years),
                        "year_start": years[0],
                        "year_end": years[-1],
                        "total_count": total,
                        "nonzero_years": n_nonzero,
                        "slope_per_year": 0.0,
                        "linregress_r": 0.0,
                        "linregress_p": 1.0,
                        "spearman_rho": 0.0,
                        "spearman_p": 1.0,
                        "kendall_tau": 0.0,
                        "kendall_p": 1.0,
                    }
                )
                pvals_for_fdr.append(1.0)
                pvals_row_idx.append(len(results) - 1)
                continue

            lr = stats.linregress(x, y_counts)
            sr = stats.spearmanr(x, y_counts)
            kt = stats.kendalltau(x, y_counts)

            results.append(
                {
                    "field": field,
                    "value": val,
                    "n_years": len(years),
                    "year_start": years[0],
                    "year_end": years[-1],
                    "total_count": total,
                    "nonzero_years": n_nonzero,
                    "slope_per_year": float(lr.slope),
                    "linregress_r": float(lr.rvalue),
                    "linregress_p": float(lr.pvalue),
                    "spearman_rho": float(sr.statistic if sr.statistic is not None else 0.0),
                    "spearman_p": float(sr.pvalue if sr.pvalue is not None else 1.0),
                    "kendall_tau": float(kt.statistic if kt.statistic is not None else 0.0),
                    "kendall_p": float(kt.pvalue if kt.pvalue is not None else 1.0),
                }
            )
            pvals_for_fdr.append(float(lr.pvalue))
            pvals_row_idx.append(len(results) - 1)

    # FDR on linregress p-values
    qvals = bh_fdr(pvals_for_fdr)
    for i, row_idx in enumerate(pvals_row_idx):
        results[row_idx]["linregress_q_fdr_bh"] = float(qvals[i])

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "field",
        "value",
        "n_years",
        "year_start",
        "year_end",
        "total_count",
        "nonzero_years",
        "slope_per_year",
        "linregress_r",
        "linregress_p",
        "linregress_q_fdr_bh",
        "spearman_rho",
        "spearman_p",
        "kendall_tau",
        "kendall_p",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in sorted(results, key=lambda x: (str(x["field"]), str(x["value"]))):
            w.writerow(r)

    sig = [
        r
        for r in results
        if float(r.get("linregress_q_fdr_bh", 1.0)) < 0.05
    ]
    sig_sorted = sorted(
        sig,
        key=lambda r: (float(r["linregress_q_fdr_bh"]), -abs(float(r["slope_per_year"]))),
    )

    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in sig_sorted:
            w.writerow(r)

    print(f"INPUT_ROWS {len(filtered)}")
    print(f"YEARS {years[0]}-{years[-1]} ({len(years)})")
    print(f"SERIES_TESTED {len(results)}")
    print(f"FDR_SIGNIFICANT {len(sig_sorted)}")
    print(f"OUT {out_path}")
    print(f"SUMMARY {summary_path}")


if __name__ == "__main__":
    main()
