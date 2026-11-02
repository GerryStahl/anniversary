import csv
from collections import Counter, defaultdict
from scipy.stats import chi2_contingency

path = "reports/trends_dataset.csv"
rows = list(csv.DictReader(open(path, encoding="utf-8")))

fields = [
    "category",
    "cluster_haiku_summary",
    "methodology_primary",
    "unit_of_analysis_primary",
    "pedagogy_primary",
    "technology_primary",
    "theory_primary",
    "ai_llm_involvement_primary",
]
eras = [
    "stahl_hesse_2006_2015",
    "ludvigsen_2016_2019",
    "rose_jarvela_2020_2023",
    "baker_reimann_2024_2027",
]

rows = [r for r in rows if r.get("year", "").isdigit() and 2006 <= int(r["year"]) <= 2025]

print("N rows:", len(rows))
print("Counts per era:")
era_counts = Counter(r["editor_era"] for r in rows)
for e in eras:
    print(f"  {e}: {era_counts[e]}")

for field in fields:
    by_era = defaultdict(Counter)
    labels = set()
    for r in rows:
        e = r["editor_era"]
        v = (r.get(field) or "").strip()
        if not v:
            continue
        by_era[e][v] += 1
        labels.add(v)

    labels = sorted(labels)
    table = [[by_era[e][lab] for lab in labels] for e in eras]
    keep = [j for j, _ in enumerate(labels) if sum(table[i][j] for i in range(len(eras))) > 0]
    labels = [labels[j] for j in keep]
    table = [[row[j] for j in keep] for row in table]

    chi2, p, dof, _ = chi2_contingency(table)
    print(f"\n[{field}] chi2 p={p:.4g}, dof={dof}, labels={len(labels)}")

    e1 = by_era[eras[0]]
    e4 = by_era[eras[3]]
    n1 = sum(e1.values()) or 1
    n4 = sum(e4.values()) or 1

    deltas = []
    for lab in labels:
        s1 = e1[lab] / n1
        s4 = e4[lab] / n4
        deltas.append((s4 - s1, lab, s1, s4))

    deltas.sort()
    low = deltas[:2]
    high = deltas[-2:]
    print("  biggest decreases/increases (share, first->last era):")
    for d, lab, s1, s4 in low + high:
        print(f"    {lab}: {s1:.3f} -> {s4:.3f} ({d:+.3f})")
