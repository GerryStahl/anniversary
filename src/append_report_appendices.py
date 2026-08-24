from pathlib import Path
import csv
from collections import defaultdict

from docx import Document
from docx.shared import Pt, Inches

REPORT_PATH = Path("reports/ijcscl_corpus_trend_report.docx")
TAXONOMY_CSV = Path("reports/dimension_taxonomy_values.csv")
PUB_SUMMARY_CSV = Path("reports/publication_trend_summary.csv")

GRAPH_CANDIDATES = [
    Path("reports/category_share_by_year.png"),
    Path("reports/year_cluster_counts_2006_2025.png"),
    Path("reports/dimension_primary_trends/methodology_year_trend.png"),
    Path("reports/embedding_drift_by_year.png"),
]


def read_taxonomy_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_pub_summary(path: Path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def add_heading(doc: Document, text: str, level: int = 1):
    p = doc.add_heading(text, level=level)
    return p


def add_appendix_taxonomy(doc: Document, taxonomy_rows: list[dict]):
    add_heading(doc, "Appendix A. Coding options", level=1)

    # legacy categories
    doc.add_paragraph("Legacy category coding (single letter):")
    for item in [
        "a = design of collaboration",
        "b = design of technology to support learning",
        "c = analysis of interaction among students",
        "d = measurement of learning",
        "e = editorial",
        "f = none of the above",
        "g = CSCL theory",
    ]:
        doc.add_paragraph(item, style="List Bullet")

    # dimensions grouped
    grouped = defaultdict(list)
    names = {}
    for r in taxonomy_rows:
        k = r["dimension_key"]
        grouped[k].append(r)
        names[k] = r["dimension_name"]

    add_heading(doc, "Appendix B. Dimension taxonomy (controlled values)", level=1)
    for dim_key in sorted(grouped.keys()):
        dim_name = names.get(dim_key, "")
        add_heading(doc, f"{dim_key} ({dim_name})", level=2)

        table = doc.add_table(rows=1, cols=3)
        table.style = "Table Grid"
        hdr = table.rows[0].cells
        hdr[0].text = "Order"
        hdr[1].text = "Option"
        hdr[2].text = "Gloss"

        rows = sorted(grouped[dim_key], key=lambda x: int(x["option_order"]))
        for r in rows:
            cells = table.add_row().cells
            cells[0].text = str(r["option_order"])
            cells[1].text = r["option"]
            cells[2].text = r.get("gloss", "")


def add_appendix_significance(doc: Document, summary_rows: list[dict]):
    add_heading(doc, "Appendix C. Significant trend results (summary)", level=1)

    if not summary_rows:
        doc.add_paragraph("No publication summary file was found.")
        return

    table = doc.add_table(rows=1, cols=6)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text = "Family"
    hdr[1].text = "Field"
    hdr[2].text = "Value"
    hdr[3].text = "Direction"
    hdr[4].text = "Effect"
    hdr[5].text = "q (FDR)"

    for r in summary_rows:
        cells = table.add_row().cells
        cells[0].text = r.get("analysis_family", "")
        cells[1].text = r.get("field", "")
        cells[2].text = r.get("value", "")
        cells[3].text = r.get("direction", "")
        cells[4].text = r.get("effect_metric", "")
        cells[5].text = r.get("q_value_fdr", "")


def add_appendix_graphs(doc: Document):
    add_heading(doc, "Appendix D. Graphs for key trends", level=1)

    added = 0
    for graph in GRAPH_CANDIDATES:
        if graph.exists():
            add_heading(doc, graph.name, level=2)
            doc.add_picture(str(graph), width=Inches(6.8))
            added += 1

    if added == 0:
        doc.add_paragraph("No graph files were found for insertion.")


def main():
    if not REPORT_PATH.exists():
        raise SystemExit(f"Report not found: {REPORT_PATH}")

    taxonomy_rows = read_taxonomy_rows(TAXONOMY_CSV)
    summary_rows = read_pub_summary(PUB_SUMMARY_CSV)

    doc = Document(str(REPORT_PATH))

    # small spacing before appendices
    doc.add_page_break()

    add_appendix_taxonomy(doc, taxonomy_rows)
    doc.add_page_break()
    add_appendix_significance(doc, summary_rows)
    doc.add_page_break()
    add_appendix_graphs(doc)

    doc.save(str(REPORT_PATH))
    print(REPORT_PATH)


if __name__ == "__main__":
    main()
