#!/usr/bin/env python3

from __future__ import annotations

import csv
from pathlib import Path

INPUT_LINEAR = Path("reports/trend_significance_tests.csv")
INPUT_SHARE = Path("reports/trend_share_tests.csv")
INPUT_MK = Path("reports/mann_kendall_theilsen.csv")
INPUT_SEG = Path("reports/segmented_regression_tests.csv")
INPUT_DRIFT = Path("reports/embedding_drift_by_year.csv")

OUT_CSV = Path("reports/publication_trend_summary.csv")
OUT_TXT = Path("reports/publication_trend_summary.txt")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


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


def fmt(x: float, digits: int = 4) -> str:
    return f"{x:.{digits}g}"


def main() -> None:
    linear = read_csv(INPUT_LINEAR)
    share = read_csv(INPUT_SHARE)
    mk = read_csv(INPUT_MK)
    seg = read_csv(INPUT_SEG)
    drift = read_csv(INPUT_DRIFT)

    rows_out: list[dict[str, str]] = []

    # 1) Count-based linear trends (already includes q)
    for r in linear:
        q = float(r.get("linregress_q_fdr_bh", "1") or 1)
        if q < 0.05:
            rows_out.append(
                {
                    "analysis_family": "count_linear",
                    "field": r["field"],
                    "value": r["value"],
                    "direction": "up" if float(r["slope_per_year"]) > 0 else "down",
                    "effect_metric": f"slope={fmt(float(r['slope_per_year']))}",
                    "p_value": fmt(float(r["linregress_p"])),
                    "q_value_fdr": fmt(q),
                    "note": "FDR-significant linear trend in yearly counts",
                }
            )

    # 2) Share-based trends (already includes q)
    for r in share:
        q = float(r.get("linregress_q_fdr_bh", "1") or 1)
        if q < 0.05:
            rows_out.append(
                {
                    "analysis_family": "share_linear",
                    "field": r["field"],
                    "value": r["value"],
                    "direction": "up" if float(r["share_slope_per_year"]) > 0 else "down",
                    "effect_metric": f"share_slope={fmt(float(r['share_slope_per_year']))}",
                    "p_value": fmt(float(r["linregress_p"])),
                    "q_value_fdr": fmt(q),
                    "note": "FDR-significant linear trend in yearly shares",
                }
            )

    # 3) Mann-Kendall + Theil-Sen (apply FDR here)
    mk_p = [float(r["kendall_p"]) for r in mk]
    mk_q = bh_fdr(mk_p)
    for r, q in zip(mk, mk_q):
        if q < 0.05:
            slope = float(r["theil_sen_slope_per_year"])
            rows_out.append(
                {
                    "analysis_family": "mann_kendall_theilsen",
                    "field": r["field"],
                    "value": r["value"],
                    "direction": "up" if slope > 0 else "down",
                    "effect_metric": f"tau={fmt(float(r['kendall_tau']))}; theil={fmt(slope)}",
                    "p_value": fmt(float(r["kendall_p"])),
                    "q_value_fdr": fmt(q),
                    "note": "FDR-significant monotonic trend",
                }
            )

    # 4) Segmented regression improvement over linear (apply FDR here)
    seg_p = [float(r["p_improved_over_linear"]) for r in seg]
    seg_q = bh_fdr(seg_p)
    for r, q in zip(seg, seg_q):
        if q < 0.05:
            rows_out.append(
                {
                    "analysis_family": "segmented_regression",
                    "field": r["field"],
                    "value": r["value"],
                    "direction": "mixed",
                    "effect_metric": (
                        f"slopes=({fmt(float(r['slope_2006_2015']))},"
                        f"{fmt(float(r['slope_2016_2019']))},"
                        f"{fmt(float(r['slope_2020_2025']))})"
                    ),
                    "p_value": fmt(float(r["p_improved_over_linear"])),
                    "q_value_fdr": fmt(q),
                    "note": "FDR-significant piecewise structure vs single linear slope",
                }
            )

    # 5) Embedding drift summary (descriptive, not p-tested)
    valid = [r for r in drift if (r.get("cosine_distance_to_2006") or "").strip()]
    if valid:
        first = valid[0]
        last = valid[-1]
        delta = float(last["cosine_distance_to_2006"]) - float(first["cosine_distance_to_2006"])
        rows_out.append(
            {
                "analysis_family": "embedding_drift",
                "field": "embedding_haiku_summary",
                "value": "centroid_distance_to_2006",
                "direction": "up" if delta > 0 else "down",
                "effect_metric": (
                    f"2006={fmt(float(first['cosine_distance_to_2006']))}; "
                    f"2025={fmt(float(last['cosine_distance_to_2006']))}; "
                    f"delta={fmt(delta)}"
                ),
                "p_value": "",
                "q_value_fdr": "",
                "note": "Descriptive semantic drift of yearly embedding centroids",
            }
        )

    # sort by family then q then p
    def key_fn(r: dict[str, str]):
        def to_num(x: str) -> float:
            try:
                return float(x)
            except Exception:
                return 999.0
        return (r["analysis_family"], to_num(r["q_value_fdr"]), to_num(r["p_value"]))

    rows_out = sorted(rows_out, key=key_fn)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "analysis_family",
            "field",
            "value",
            "direction",
            "effect_metric",
            "p_value",
            "q_value_fdr",
            "note",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_out)

    # short text summary
    by_family = {}
    for r in rows_out:
        by_family[r["analysis_family"]] = by_family.get(r["analysis_family"], 0) + 1

    lines = [
        "Publication-ready trend summary",
        f"Total retained findings: {len(rows_out)}",
        "Counts by analysis family:",
    ]
    for fam in sorted(by_family):
        lines.append(f"  - {fam}: {by_family[fam]}")

    OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"OUT_CSV {OUT_CSV}")
    print(f"OUT_TXT {OUT_TXT}")
    print(f"RETAINED {len(rows_out)}")


if __name__ == "__main__":
    main()
