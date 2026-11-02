#!/usr/bin/env python3

from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from src.store import load_store
from src.trend_filters import is_excluded_trend_row

INPUT = Path("reports/trends_dataset.csv")  # non-editorials by default
OUT_SEG = Path("reports/segmented_regression_tests.csv")
OUT_MK = Path("reports/mann_kendall_theilsen.csv")
OUT_DRIFT = Path("reports/embedding_drift_by_year.csv")
OUT_DRIFT_PNG = Path("reports/embedding_drift_by_year.png")

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

YEAR_START = 2006
YEAR_END = 2025
KNOTS = [2016, 2020]  # fixed editor-era boundary years with enough post-years in range


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        if is_excluded_trend_row(r):
            continue
        try:
            y = int(r.get("year", ""))
        except Exception:
            continue
        if YEAR_START <= y <= YEAR_END:
            out.append(r)
    return out


def build_share_series(rows: list[dict[str, str]]):
    years = list(range(YEAR_START, YEAR_END + 1))
    totals = Counter(int(r["year"]) for r in rows)
    series = []

    for field in FIELDS:
        labels = sorted({(r.get(field) or "").strip() for r in rows if (r.get(field) or "").strip()})
        for label in labels:
            y_counts = Counter(
                int(r["year"]) for r in rows if (r.get(field) or "").strip() == label
            )
            y = np.array([(y_counts[yr] / totals[yr]) if totals[yr] > 0 else 0.0 for yr in years], dtype=float)
            series.append((field, label, years, y))

    return series


def linear_fit(x: np.ndarray, y: np.ndarray):
    X = np.column_stack([np.ones_like(x), x])
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ beta
    rss = float(np.sum((y - yhat) ** 2))
    return beta, yhat, rss


def segmented_fit(x_year: np.ndarray, y: np.ndarray, knots: list[int]):
    x = x_year.astype(float)
    cols = [np.ones_like(x), x]
    for k in knots:
        cols.append(np.maximum(0.0, x - float(k)))
    X = np.column_stack(cols)
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ beta
    rss = float(np.sum((y - yhat) ** 2))
    return beta, yhat, rss, X.shape[1]


def f_test_nested(rss_reduced: float, rss_full: float, p_reduced: int, p_full: int, n: int):
    df1 = p_full - p_reduced
    df2 = n - p_full
    if df1 <= 0 or df2 <= 0:
        return 1.0, 1.0
    num = (rss_reduced - rss_full) / df1
    den = rss_full / df2 if rss_full > 0 else 1e-12
    f_stat = max(num / den, 0.0)
    p = float(1.0 - stats.f.cdf(f_stat, df1, df2))
    return float(f_stat), p


def run_segmented_regression(series):
    results = []
    for field, label, years, y in series:
        x_idx = np.arange(len(years), dtype=float)
        x_year = np.array(years, dtype=float)

        b_lin, _, rss_lin = linear_fit(x_idx, y)
        b_seg, _, rss_seg, p_full = segmented_fit(x_year, y, KNOTS)

        f_stat, p = f_test_nested(
            rss_reduced=rss_lin,
            rss_full=rss_seg,
            p_reduced=2,
            p_full=p_full,
            n=len(y),
        )

        # piecewise slopes per segment
        slope1 = b_seg[1]
        slope2 = b_seg[1] + (b_seg[2] if len(b_seg) > 2 else 0.0)
        slope3 = b_seg[1] + (b_seg[2] if len(b_seg) > 2 else 0.0) + (b_seg[3] if len(b_seg) > 3 else 0.0)

        results.append(
            {
                "field": field,
                "value": label,
                "n_years": len(y),
                "linear_slope_per_index": float(b_lin[1]),
                "rss_linear": rss_lin,
                "rss_segmented": rss_seg,
                "f_stat": f_stat,
                "p_improved_over_linear": p,
                "slope_2006_2015": float(slope1),
                "slope_2016_2019": float(slope2),
                "slope_2020_2025": float(slope3),
            }
        )
    return results


def run_mk_theilsen(series):
    results = []
    x = np.arange(YEAR_START, YEAR_END + 1, dtype=float)
    for field, label, years, y in series:
        tau = stats.kendalltau(x, y)
        ts = stats.theilslopes(y, x, 0.95)
        results.append(
            {
                "field": field,
                "value": label,
                "n_years": len(y),
                "kendall_tau": float(tau.statistic if tau.statistic is not None else 0.0),
                "kendall_p": float(tau.pvalue if tau.pvalue is not None else 1.0),
                "theil_sen_slope_per_year": float(ts.slope),
                "theil_sen_intercept": float(ts.intercept),
                "theil_sen_low_slope": float(ts.low_slope),
                "theil_sen_high_slope": float(ts.high_slope),
            }
        )
    return results


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def run_embedding_drift(rows: list[dict[str, str]]):
    store = load_store()

    by_year_ids: dict[int, list[str]] = defaultdict(list)
    for r in rows:
        by_year_ids[int(r["year"])].append(r["id"])

    years = list(range(YEAR_START, YEAR_END + 1))
    centroids: dict[int, np.ndarray] = {}
    dispersions: dict[int, float] = {}

    for y in years:
        vecs = []
        for aid in by_year_ids.get(y, []):
            article = store.get(aid)
            if article is None:
                continue
            emb = article.embedding_haiku_summary
            if emb is None:
                continue
            vec = np.asarray(emb, dtype=float)
            vecs.append(vec)

        if not vecs:
            continue

        mat = np.vstack(vecs)
        centroid = mat.mean(axis=0)
        centroids[y] = centroid

        # mean cosine distance to centroid
        dists = [1.0 - cosine(v, centroid) for v in mat]
        dispersions[y] = float(np.mean(dists)) if dists else 0.0

    base_year = years[0]
    base_centroid = centroids.get(base_year)

    out = []
    prev_centroid = None
    for y in years:
        c = centroids.get(y)
        if c is None:
            out.append(
                {
                    "year": y,
                    "n_articles": len(by_year_ids.get(y, [])),
                    "cosine_distance_to_prev_year": "",
                    "cosine_distance_to_2006": "",
                    "within_year_mean_cosine_distance": "",
                }
            )
            continue

        to_prev = ""
        if prev_centroid is not None:
            to_prev = 1.0 - cosine(c, prev_centroid)

        to_base = ""
        if base_centroid is not None:
            to_base = 1.0 - cosine(c, base_centroid)

        out.append(
            {
                "year": y,
                "n_articles": len(by_year_ids.get(y, [])),
                "cosine_distance_to_prev_year": to_prev,
                "cosine_distance_to_2006": to_base,
                "within_year_mean_cosine_distance": dispersions.get(y, ""),
            }
        )
        prev_centroid = c

    # chart
    ys = [r["year"] for r in out if isinstance(r["cosine_distance_to_2006"], float)]
    d_base = [r["cosine_distance_to_2006"] for r in out if isinstance(r["cosine_distance_to_2006"], float)]
    d_prev = [r["cosine_distance_to_prev_year"] for r in out if isinstance(r["cosine_distance_to_prev_year"], float)]
    ys_prev = [r["year"] for r in out if isinstance(r["cosine_distance_to_prev_year"], float)]
    disp = [r["within_year_mean_cosine_distance"] for r in out if isinstance(r["within_year_mean_cosine_distance"], float)]

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(12, 7))
    if ys:
        ax.plot(ys, d_base, marker="o", linewidth=2, label="distance to 2006 centroid")
    if ys_prev:
        ax.plot(ys_prev, d_prev, marker="s", linewidth=2, label="distance to previous year")
    if ys:
        ax.plot(ys, disp, marker="^", linewidth=2, label="within-year dispersion")
    ax.set_title("Embedding drift indicators by year (haiku summary embeddings)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Cosine distance")
    ax.set_xticks(list(range(YEAR_START, YEAR_END + 1)))
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    fig.tight_layout()
    OUT_DRIFT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DRIFT_PNG, dpi=200, bbox_inches="tight")
    plt.close(fig)

    return out


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    rows = read_rows(INPUT)
    series = build_share_series(rows)

    seg = run_segmented_regression(series)
    mk = run_mk_theilsen(series)
    drift = run_embedding_drift(rows)

    write_csv(OUT_SEG, seg)
    write_csv(OUT_MK, mk)
    write_csv(OUT_DRIFT, drift)

    print(f"INPUT_ROWS {len(rows)}")
    print(f"SERIES {len(series)}")
    print(f"OUT_SEG {OUT_SEG}")
    print(f"OUT_MK {OUT_MK}")
    print(f"OUT_DRIFT {OUT_DRIFT}")
    print(f"OUT_DRIFT_PNG {OUT_DRIFT_PNG}")


if __name__ == "__main__":
    main()
