#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from scipy import stats

DEFAULT_INPUT = Path("reports/trends_dataset.csv")
OUT_SHARE = Path("reports/trend_share_tests.csv")
OUT_SHARE_SIG = Path("reports/trend_share_significant.csv")
OUT_ENTROPY = Path("reports/yearly_entropy_by_field.csv")
OUT_ENTROPY_PNG = Path("reports/yearly_entropy_by_field.png")
OUT_CATEGORY_SHARE_PNG = Path("reports/category_share_by_year.png")

FIELDS = [
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
    p = argparse.ArgumentParser(description="Compute additional trend indicators (share-based tests + entropy).")
    p.add_argument("--input", default=str(DEFAULT_INPUT))
    p.add_argument("--year-start", type=int, default=2006)
    p.add_argument("--year-end", type=int, default=2025)
    return p.parse_args()


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
    for i, idx in enumerate(order):
        out[idx] = q[i]
    return out


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def entropy_from_counts(counts: Counter[str]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        if c <= 0:
            continue
        p = c / total
        h -= p * math.log(p)
    return h


def main() -> None:
    args = parse_args()
    rows = read_rows(Path(args.input))

    filtered = []
    for r in rows:
        try:
            y = int(r.get("year", ""))
        except Exception:
            continue
        if args.year_start <= y <= args.year_end:
            filtered.append(r)

    years = list(range(args.year_start, args.year_end + 1))
    x = list(range(len(years)))

    # denominator: article count per year (non-editorials already in input)
    year_totals = Counter()
    for r in filtered:
        year_totals[int(r["year"])] += 1

    # share tests
    share_results = []
    pvals = []
    pidx = []

    for field in FIELDS:
        values = sorted({(r.get(field) or "").strip() for r in filtered if (r.get(field) or "").strip()})
        for v in values:
            y_counts = Counter()
            for r in filtered:
                y = int(r["year"])
                if (r.get(field) or "").strip() == v:
                    y_counts[y] += 1

            shares = []
            raw_counts = []
            for y in years:
                total = year_totals[y]
                c = y_counts[y]
                raw_counts.append(c)
                shares.append((c / total) if total > 0 else 0.0)

            if len(set(shares)) <= 1:
                lr_p = 1.0
                lr_r = 0.0
                lr_slope = 0.0
                sp_rho = 0.0
                sp_p = 1.0
            else:
                lr = stats.linregress(x, shares)
                sp = stats.spearmanr(x, shares)
                lr_p = float(lr.pvalue)
                lr_r = float(lr.rvalue)
                lr_slope = float(lr.slope)
                sp_rho = float(sp.statistic if sp.statistic is not None else 0.0)
                sp_p = float(sp.pvalue if sp.pvalue is not None else 1.0)

            row = {
                "field": field,
                "value": v,
                "n_years": len(years),
                "year_start": years[0],
                "year_end": years[-1],
                "total_count": sum(raw_counts),
                "mean_share": sum(shares) / len(shares),
                "share_slope_per_year": lr_slope,
                "linregress_r": lr_r,
                "linregress_p": lr_p,
                "spearman_rho": sp_rho,
                "spearman_p": sp_p,
            }
            share_results.append(row)
            pvals.append(lr_p)
            pidx.append(len(share_results) - 1)

    qvals = bh_fdr(pvals)
    for i, ridx in enumerate(pidx):
        share_results[ridx]["linregress_q_fdr_bh"] = qvals[i]

    OUT_SHARE.parent.mkdir(parents=True, exist_ok=True)
    share_fields = [
        "field",
        "value",
        "n_years",
        "year_start",
        "year_end",
        "total_count",
        "mean_share",
        "share_slope_per_year",
        "linregress_r",
        "linregress_p",
        "linregress_q_fdr_bh",
        "spearman_rho",
        "spearman_p",
    ]
    with OUT_SHARE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=share_fields)
        w.writeheader()
        for r in sorted(share_results, key=lambda z: (z["field"], z["value"])):
            w.writerow(r)

    sig = [r for r in share_results if float(r["linregress_q_fdr_bh"]) < 0.05]
    sig.sort(key=lambda z: (z["linregress_q_fdr_bh"], -abs(float(z["share_slope_per_year"])) ))
    with OUT_SHARE_SIG.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=share_fields)
        w.writeheader()
        w.writerows(sig)

    # entropy by field and year
    entropy_rows = []
    ent_by_field = {f: [] for f in FIELDS}
    for field in FIELDS:
        all_values = sorted({(r.get(field) or "").strip() for r in filtered if (r.get(field) or "").strip()})
        k = max(len(all_values), 1)
        max_h = math.log(k)
        for y in years:
            counts = Counter((r.get(field) or "").strip() for r in filtered if int(r["year"]) == y and (r.get(field) or "").strip())
            h = entropy_from_counts(counts)
            h_norm = (h / max_h) if max_h > 0 else 0.0
            entropy_rows.append({
                "field": field,
                "year": y,
                "entropy": h,
                "entropy_normalized": h_norm,
                "n_labels": len([k2 for k2, v2 in counts.items() if v2 > 0]),
                "year_total": year_totals[y],
            })
            ent_by_field[field].append((y, h_norm))

    with OUT_ENTROPY.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["field", "year", "entropy", "entropy_normalized", "n_labels", "year_total"])
        w.writeheader()
        w.writerows(entropy_rows)

    # entropy chart
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(12, 7))
    for field in FIELDS:
        ys = [p[0] for p in ent_by_field[field]]
        hs = [p[1] for p in ent_by_field[field]]
        ax.plot(ys, hs, marker="o", linewidth=1.8, label=field)
    ax.set_title("Normalized label entropy by year (non-editorials)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Normalized entropy (0-1)")
    ax.set_xticks(years)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT_ENTROPY_PNG, dpi=200, bbox_inches="tight")
    plt.close(fig)

    # category share chart
    cat_values = sorted({(r.get("category") or "").strip() for r in filtered if (r.get("category") or "").strip()})
    fig2, ax2 = plt.subplots(figsize=(12, 7))
    for c in cat_values:
        pts = []
        for y in years:
            total = year_totals[y]
            num = sum(1 for r in filtered if int(r["year"]) == y and (r.get("category") or "").strip() == c)
            pts.append((num / total) if total > 0 else 0.0)
        ax2.plot(years, pts, marker="o", linewidth=2, label=c)
    ax2.set_title("Category share by year (non-editorials)")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Share of articles")
    ax2.set_xticks(years)
    ax2.tick_params(axis="x", rotation=45)
    ax2.legend(title="category", loc="upper left", bbox_to_anchor=(1.02, 1))
    fig2.tight_layout()
    fig2.savefig(OUT_CATEGORY_SHARE_PNG, dpi=200, bbox_inches="tight")
    plt.close(fig2)

    print(f"INPUT_ROWS {len(filtered)}")
    print(f"YEARS {years[0]}-{years[-1]} ({len(years)})")
    print(f"SERIES_TESTED {len(share_results)}")
    print(f"FDR_SIGNIFICANT {len(sig)}")
    print(f"OUT_SHARE {OUT_SHARE}")
    print(f"OUT_SHARE_SIG {OUT_SHARE_SIG}")
    print(f"OUT_ENTROPY {OUT_ENTROPY}")
    print(f"OUT_ENTROPY_PNG {OUT_ENTROPY_PNG}")
    print(f"OUT_CATEGORY_SHARE_PNG {OUT_CATEGORY_SHARE_PNG}")


if __name__ == "__main__":
    main()
