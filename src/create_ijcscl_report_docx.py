from pathlib import Path
from docx import Document
from docx.shared import Pt

out = Path("reports/ijcscl_corpus_trend_report.docx")
out.parent.mkdir(parents=True, exist_ok=True)

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)

doc.add_heading("Twenty Years of ijCSCL: A Computational Trend Analysis (2006–2025)", 0)

doc.add_heading("1) Project overview", level=1)
doc.add_paragraph(
    "This project analyzed the International Journal of Computer-Supported Collaborative Learning (ijCSCL) corpus across two decades using a reproducible pipeline that combines language-model coding with statistical trend testing. The goal was to characterize how the journal's thematic, methodological, and conceptual profile changed over time."
)
doc.add_paragraph(
    "The workflow produced standardized article summaries, semantic embeddings, unsupervised clusters, category labels, six-dimension primary/secondary coding, and multiple trend-significance analyses."
)

doc.add_heading("2) Data and scope", level=1)
doc.add_paragraph(
    "The working corpus contains 470 articles (including editorials). For trend analyses, editorials were excluded to reduce confounding from front-matter changes. Most statistical trend tests were run on non-editorial records from 2006–2025, yielding 20 yearly data points."
)

doc.add_heading("3) Summary generation", level=1)
doc.add_paragraph("Summaries were used as a normalized representation of each article for coding and semantic analysis.")
doc.add_paragraph("Summarization prompt used in the pipeline:")
quote = doc.add_paragraph(
    "You are an expert in computer-supported collaborative learning. Write a concise 50-60 word summary of the article's central claim or finding. Focus on the main research question, method type, and conclusion. Do not mention that you are summarizing. Return only the summary text."
)
quote.style = doc.styles["Intense Quote"] if "Intense Quote" in doc.styles else doc.styles["Normal"]

doc.add_heading("4) Embedding semantic vectors and clustering", level=1)
doc.add_paragraph(
    "Article summaries (summary_haiku) were embedded with all-MiniLM-L6-v2 (384 dimensions). KMeans clustering was applied, and silhouette-based model selection identified k=2 as the strongest global split, with useful secondary granularity near k=7."
)
doc.add_paragraph(
    "Cluster trend outputs were generated as yearly line charts and tabular counts, including dedicated exports for k=2, k=5, and k=7 analyses."
)

doc.add_heading("5) Category coding", level=1)
doc.add_paragraph(
    "Legacy categories were recomputed using summary_haiku via Claude Haiku with explicit support for a new category g (CSCL theory). A rule-based override assigned category e to any article with a non-null editorial field."
)
doc.add_paragraph("Final category counts after reclassification: a=105, b=58, c=116, d=52, e=83, f=1, g=55.")

doc.add_heading("6) Six-dimension coding (primary and secondary)", level=1)
doc.add_paragraph(
    "Each article was coded across six dimensions: methodology, unit of analysis, pedagogy, technology, theory, and AI/LLM involvement. For each dimension, one primary value and up to two secondary values were assigned from controlled taxonomies, along with evidence_span, coding_confidence, and coding_notes."
)
doc.add_paragraph(
    "Coding used summary_haiku as the primary source, with full-text fallback when needed. All 470 articles were successfully coded and written back to the canonical store."
)

doc.add_heading("7) Trend analyses conducted", level=1)
for item in [
    "Linear count trends with multiple-testing correction (BH-FDR).",
    "Linear share trends (proportion per year) with BH-FDR correction.",
    "Mann–Kendall monotonic trend tests with Theil–Sen robust slope estimation.",
    "Segmented regression (era-sensitive piecewise slopes, with knots at 2016 and 2020).",
    "Embedding drift analysis via centroid cosine distance and within-year semantic dispersion.",
    "Editor-era transition diagnostics using chi-square distribution tests across eras.",
]:
    doc.add_paragraph(item, style="List Bullet")

doc.add_heading("8) Main findings and significance", level=1)
doc.add_paragraph(
    "Across robust, FDR-controlled tests, two convergent longitudinal trends were identified: (1) decline in methodology_primary = ethnographic_case_study, significant in count-based, share-based, and Mann–Kendall/Theil–Sen analyses; and (2) increase in cluster_haiku_summary = 1, significant in share-based and Mann–Kendall/Theil–Sen analyses."
)
doc.add_paragraph(
    "Embedding-based measures showed only modest, non-monotonic change in the corpus's average semantic content: distance from the 2006 baseline rose slightly through 2023 but returned to earlier levels by 2025. Because no significance test was applied and yearly samples are small, this is weak, suggestive evidence at most."
)

doc.add_heading("9) Interpretation", level=1)
doc.add_paragraph(
    "The combined evidence suggests a gradual methodological and thematic reconfiguration of the ijCSCL corpus over the 20-year period. The strongest quantitative evidence points to reduced prevalence of ethnographic-case-study labeling and increased prevalence of one dominant semantic cluster profile. Era transition checks further indicate shifts in method, pedagogy, and technology distributions aligned with editorial periods, though these remain exploratory unless confirmed in fully preregistered models."
)

doc.add_heading("10) Limitations and next steps", level=1)
doc.add_paragraph(
    "Because the coding pipeline uses model-assisted labels, reliability checks remain important. Recommended next steps include human adjudication on a stratified sample, compositional trend models for share data, formal change-point models at editor transitions, and expanded embedding-drift diagnostics with confidence intervals."
)

doc.save(out)
print(out)
