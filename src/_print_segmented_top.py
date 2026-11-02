import csv

rows = list(csv.DictReader(open('reports/segmented_regression_tests.csv', encoding='utf-8')))
rows.sort(key=lambda r: float(r['p_improved_over_linear']))
for r in rows[:15]:
    print(
        f"{r['field']}|{r['value']}|p={float(r['p_improved_over_linear']):.4g}|"
        f"slopes=({float(r['slope_2006_2015']):+.4f},{float(r['slope_2016_2019']):+.4f},{float(r['slope_2020_2025']):+.4f})"
    )
