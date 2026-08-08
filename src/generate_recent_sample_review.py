import json
import random
from pathlib import Path

from src.dimension_taxonomy import TAXONOMY
from src.llm import ollama_chat
from src.store import load_store
from src.summarize import SUMMARIZATION_SYSTEM_PROMPT


RANDOM_SEED = 42
RECENT_YEARS = {2022, 2023, 2024, 2025, 2026}
MODEL = "llama3.1:8b"
REPORT_MD = Path("reports/recent5yr_sample_review.md")
REPORT_JSON = Path("reports/recent5yr_sample_review.json")


def _build_trend_system_prompt() -> str:
    """Build the trend-coding system prompt with the controlled taxonomy options embedded."""
    dim_lines = []
    for dim_key in ("methodology", "unit_of_analysis", "pedagogy", "technology", "theory", "ai_llm_involvement"):
        dim = TAXONOMY[dim_key]
        options_str = ", ".join(dim.options)
        dim_lines.append(f"  {dim_key}_primary: one of [{options_str}]")
    dims_block = "\n".join(dim_lines)

    return f"""
You are an expert in computer-supported collaborative learning and trend coding.
Return a compact JSON object with exactly these keys and controlled values:

{dims_block}
  evidence_span: short phrase indicating which sections of the paper support the coding, e.g. "methods+findings"
  coding_confidence: a decimal between 0.0 and 1.0
  coding_notes: one sentence noting rationale or any uncertainty

Rules:
- You MUST choose values from the listed options for each *_primary field. Do not invent new labels.
- If no option fits well, pick the closest one and explain in coding_notes.
- Return only valid JSON. No markdown fences, no commentary outside the JSON object.
""".strip()


trend_system_prompt = _build_trend_system_prompt()


def format_authors(article) -> str:
    if isinstance(article.authors, list):
        return " & ".join(str(x) for x in article.authors if str(x).strip())
    return str(article.authors or "Unknown")


def build_user_prompt(article) -> str:
    text = article.fulltext or ""
    snippet = text[:12000]
    return f"""
Title: {article.title or ''}
Authors: {format_authors(article)}
Year: {article.year or ''}
Volume: {article.volume or ''}
Issue: {article.issue or ''}
Article ID: {article.id}

Article excerpt:
{snippet}
""".strip()


def extract_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Fallback: try the whole string once
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Unable to parse JSON from model output: {exc}") from exc


def generate_review_sample() -> dict:
    random.seed(RANDOM_SEED)
    store = load_store()
    candidates = [
        article
        for article in store.values()
        if article.fulltext
        and article.year in RECENT_YEARS
        and (article.editorial or "").lower() != "editorial"
    ]
    sample = random.sample(candidates, 5)
    sample.sort(key=lambda a: (a.year, a.volume, a.issue, a.article_number, a.id))

    rows = []
    for article in sample:
        general_summary = ollama_chat(
            model=MODEL,
            system_prompt=SUMMARIZATION_SYSTEM_PROMPT,
            user_prompt=build_user_prompt(article),
            temperature=0.2,
        )
        coding_json = ollama_chat(
            model=MODEL,
            system_prompt=trend_system_prompt,
            user_prompt=build_user_prompt(article),
            temperature=0.2,
        )
        parsed_coding = {}
        try:
            parsed_coding = extract_json_object(coding_json)
        except Exception:
            parsed_coding = {"raw_response": coding_json}

        rows.append(
            {
                "id": article.id,
                "year": article.year,
                "volume": article.volume,
                "issue": article.issue,
                "article_number": article.article_number,
                "title": article.title,
                "authors": format_authors(article),
                "general_summary": general_summary,
                "trend_coding": parsed_coding,
            }
        )

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# Recent 5-year review sample")
    lines.append("")
    lines.append("These are draft outputs for a random sample of 5 non-editorial articles from 2022–2026. Please review especially the trend-coding values.")
    lines.append("")
    for idx, row in enumerate(rows, 1):
        lines.append(f"## {idx}. {row['title'] or '[No title]'}")
        lines.append(f"- ID: `{row['id']}`")
        lines.append(f"- Year: {row['year']} | Volume: {row['volume']} | Issue: {row['issue']} | Article number: {row['article_number']}")
        lines.append(f"- Authors: {row['authors']}")
        lines.append("- General summary:")
        lines.append(f"  - {row['general_summary']}")
        lines.append("- Trend coding draft:")
        coding = row['trend_coding']
        if isinstance(coding, dict):
            for key in [
                'methodology_primary',
                'unit_of_analysis_primary',
                'pedagogy_primary',
                'technology_primary',
                'theory_primary',
                'ai_llm_involvement_primary',
                'evidence_span',
                'coding_confidence',
                'coding_notes',
            ]:
                value = coding.get(key, '')
                lines.append(f"  - {key}: {value}")
        else:
            lines.append(f"  - {coding}")
        lines.append("")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    REPORT_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"rows": rows, "report_md": str(REPORT_MD), "report_json": str(REPORT_JSON)}


if __name__ == "__main__":
    result = generate_review_sample()
    print("REPORT_MD", result["report_md"])
    print("REPORT_JSON", result["report_json"])
    for row in result["rows"]:
        print("---")
        print(row["id"], row["title"])
        print(row["general_summary"])
        print(row["trend_coding"])
