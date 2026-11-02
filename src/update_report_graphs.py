#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Inches


REPORT_PATH = Path("reports/ijcscl_corpus_trend_report.docx")
GRAPH_CANDIDATES = [
    (Path("reports/category_share_by_year.png"), "Category share by year"),
    (Path("reports/year_cluster_counts_2006_2025.png"), "Semantic cluster counts by year (k=7)"),
    (Path("reports/dimension_primary_trends/methodology_year_trend.png"), "Primary methodology by year"),
    (Path("reports/dimension_primary_trends/unit_of_analysis_year_trend.png"), "Primary unit of analysis by year"),
    (Path("reports/dimension_primary_trends/pedagogy_year_trend.png"), "Primary pedagogy by year"),
    (Path("reports/dimension_primary_trends/technology_year_trend.png"), "Primary technology by year"),
    (Path("reports/dimension_primary_trends/theory_year_trend.png"), "Primary theoretical framework by year"),
    (Path("reports/dimension_primary_trends/ai_llm_involvement_year_trend.png"), "Primary AI/LLM involvement by year"),
    (Path("reports/embedding_drift_by_year.png"), "Embedding drift indicators by year"),
]


def replace_graph_appendix() -> None:
    missing = [str(path) for path, _ in GRAPH_CANDIDATES if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Required report graphs are missing: {', '.join(missing)}")

    document = Document(str(REPORT_PATH))
    appendix = next(
        (paragraph for paragraph in document.paragraphs if paragraph.text.startswith("Appendix D.")),
        None,
    )
    if appendix is None:
        raise ValueError("Could not find Appendix D in the report")

    appendix.clear()
    appendix.add_run("Appendix D. Non-editorial and non-erratum trends (2006-2025)")

    body = document._body._element
    children = list(body)
    appendix_index = children.index(appendix._p)
    for element in children[appendix_index + 1 :]:
        if element.tag.endswith("}sectPr"):
            continue
        body.remove(element)

    document.add_paragraph(
        "These figures exclude records marked as editorial, corrected, or book review, "
        "records with article number 0, and category e/f records. The category chart shows "
        "annual shares; the other charts show annual counts or embedding distances."
    )
    for path, caption in GRAPH_CANDIDATES:
        document.add_heading(caption, level=2)
        document.add_picture(str(path), width=Inches(6.2))

    document.save(str(REPORT_PATH))

    verified = Document(str(REPORT_PATH))
    headings = [paragraph.text for paragraph in verified.paragraphs]
    if not any(text.startswith("Appendix D. Non-editorial") for text in headings):
        raise ValueError("Updated Appendix D heading did not persist")
    if sum(len(paragraph._p.xpath(".//a:blip")) for paragraph in verified.paragraphs) != len(GRAPH_CANDIDATES):
        raise ValueError("Updated Appendix D does not contain all expected graphs")

    print(f"REPORT {REPORT_PATH}")
    print(f"GRAPHS_INSERTED {len(GRAPH_CANDIDATES)}")


if __name__ == "__main__":
    replace_graph_appendix()
