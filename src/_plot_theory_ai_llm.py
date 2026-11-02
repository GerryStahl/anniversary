import sys
from collections import Counter

import matplotlib.pyplot as plt

sys.path.insert(0, ".")
import src.store as s


def build_series(rows, years, field_name):
    labels = sorted({getattr(a, field_name) or "uncoded" for a in rows})
    by_year_label = {y: Counter() for y in years}
    for a in rows:
        label = getattr(a, field_name) or "uncoded"
        by_year_label[a.year][label] += 1
    series = {label: [by_year_label[y][label] for y in years] for label in labels}
    return labels, series


def plot_stacked(ax, years, labels, series, title, legend_title):
    bottoms = [0] * len(years)
    cmap = plt.get_cmap("tab20")
    for i, label in enumerate(labels):
        vals = series[label]
        ax.bar(years, vals, bottom=bottoms, label=label, color=cmap(i % 20), width=0.8)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax.set_title(title, fontsize=12)
    ax.set_xlabel("Year")
    ax.set_ylabel("Article count")
    ax.set_xticks(years)
    ax.set_xticklabels(years, rotation=45, ha="right")
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    ax.legend(title=legend_title, bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)


articles = s.load_store().values()
rows = [a for a in articles if a.year is not None and a.editorial != "editorial"]
years = sorted({a.year for a in rows})

theory_labels, theory_series = build_series(rows, years, "theory_primary")
ai_labels, ai_series = build_series(rows, years, "ai_llm_involvement_primary")

fig, axes = plt.subplots(2, 1, figsize=(16, 11), constrained_layout=True)
plot_stacked(
    axes[0],
    years,
    theory_labels,
    theory_series,
    "CSCL Theory Dimension by Year (Primary Code)",
    "Theory",
)
plot_stacked(
    axes[1],
    years,
    ai_labels,
    ai_series,
    "AI/LLM Involvement Dimension by Year (Primary Code)",
    "AI/LLM",
)

out = "reports/year_theory_ai_llm_dimensions.png"
fig.savefig(out, dpi=180)
print("Saved", out)
