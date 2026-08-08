"""
Generate Claude Haiku summaries + taxonomy-constrained dimension coding
for the same 5 sample articles used in the trend-coding review, then
write a combined comparison report.

Run with:
  ANTHROPIC_API_KEY=... PYTHONPATH=$PWD python src/_run_haiku_and_coding_sample.py
"""
import json
import os
import random
from pathlib import Path

from anthropic import Anthropic

from src.dimension_taxonomy import TAXONOMY
from src.llm import ollama_chat
from src.store import load_store
from src.summarize import (
    SUMMARIZATION_SYSTEM_PROMPT,
    build_summarization_prompt,
    clean_summary,
)

RANDOM_SEED = 42
RECENT_YEARS = {2022, 2023, 2024, 2025, 2026}
HAIKU_MODEL = "claude-haiku-4-5"
OLLAMA_SUMMARY_MODEL = "llama3.1:8b"
REPORT_MD = Path("reports/recent5yr_sample_ollama_vs_haiku.md")
REPORT_JSON = Path("reports/recent5yr_sample_combined.json")


# ── Taxonomy-constrained coding prompt ────────────────────────────────────────

def _build_trend_system_prompt() -> str:
    blocks = []
    for dim_key in (
        "methodology",
        "unit_of_analysis",
        "pedagogy",
        "technology",
        "theory",
        "ai_llm_involvement",
    ):
        dim = TAXONOMY[dim_key]
        blocks.append(f"  {dim_key}_primary — choose ONE of:\n{dim.prompt_block()}")
    dims_block = "\n".join(blocks)
    return f"""You are an expert in computer-supported collaborative learning (CSCL) and systematic literature review.
Return a compact JSON object with exactly these keys and controlled values:

{dims_block}
  evidence_span: short phrase indicating which sections support the coding, e.g. "methods+findings"
  coding_confidence: a decimal between 0.0 and 1.0
  coding_notes: one or two sentences noting rationale or uncertainty

Rules:
- You MUST choose values from the listed options for each *_primary field. Do not invent labels.
- If no option fits well, choose "other" and explain in coding_notes.
- Return only valid JSON. No markdown fences, no extra text outside the JSON object."""


TREND_SYSTEM_PROMPT = _build_trend_system_prompt()


# ── Helpers ───────────────────────────────────────────────────────────────────

def format_authors(article) -> str:
    if isinstance(article.authors, list):
        return " & ".join(str(x) for x in article.authors if str(x).strip())
    return str(article.authors or "Unknown")


def build_coding_prompt(article) -> str:
    snippet = (article.fulltext or "")[:12000]
    return f"""Title: {article.title or ''}
Authors: {format_authors(article)}
Year: {article.year or ''}
Volume: {article.volume or ''}
Issue: {article.issue or ''}
Article ID: {article.id}

Article excerpt:
{snippet}""".strip()


def extract_json(text: str) -> dict:
    cleaned = text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start: end + 1])
        except json.JSONDecodeError:
            pass
    return json.loads(cleaned)


def haiku_summary(client: Anthropic, article) -> str:
    user_prompt = build_summarization_prompt(article)
    response = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=220,
        temperature=0.2,
        system=SUMMARIZATION_SYSTEM_PROMPT + "\nDo not include headers or section titles. Return only the summary text.",
        messages=[{"role": "user", "content": user_prompt}],
    )
    parts = [b.text for b in response.content if getattr(b, "type", "") == "text"]
    return clean_summary(" ".join(parts))


def haiku_coding(client: Anthropic, article) -> dict:
    response = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=600,
        temperature=0.2,
        system=TREND_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_coding_prompt(article)}],
    )
    parts = [b.text for b in response.content if getattr(b, "type", "") == "text"]
    raw = " ".join(parts)
    try:
        return extract_json(raw)
    except Exception:
        return {"raw_response": raw}


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set.")
    client = Anthropic(api_key=api_key)

    random.seed(RANDOM_SEED)
    store = load_store()
    candidates = [
        a for a in store.values()
        if a.fulltext
        and a.year in RECENT_YEARS
        and (a.editorial or "").lower() != "editorial"
    ]
    sample = random.sample(candidates, 5)
    sample.sort(key=lambda a: (a.year, a.volume, a.issue, a.article_number, a.id))

    results = []
    for idx, a in enumerate(sample, 1):
        print(f"\n[{idx}/5] {a.title or a.id[:70]}")

        print("  → Haiku summary …")
        h_summary = haiku_summary(client, a)
        print(f"     {h_summary[:90]}…")

        print("  → Ollama summary …")
        o_summary = clean_summary(
            ollama_chat(
                model=OLLAMA_SUMMARY_MODEL,
                system_prompt=SUMMARIZATION_SYSTEM_PROMPT,
                user_prompt=build_coding_prompt(a),
                temperature=0.2,
            )
        )

        print("  → Dimension coding …")
        coding = haiku_coding(client, a)
        print(f"     methodology={coding.get('methodology_primary','?')}  "
              f"theory={coding.get('theory_primary','?')}  "
              f"confidence={coding.get('coding_confidence','?')}")

        results.append({
            "id": a.id,
            "year": a.year,
            "volume": a.volume,
            "issue": a.issue,
            "article_number": a.article_number,
            "title": a.title,
            "authors": format_authors(a),
            "summary_haiku": h_summary,
            "summary_ollama": o_summary,
            "trend_coding": coding,
        })

    # ── Write JSON ────────────────────────────────────────────────────────────
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── Write Markdown ────────────────────────────────────────────────────────
    lines = [
        "# Sample review: Haiku dimension coding + Ollama & Haiku summaries",
        "",
        f"Same 5 articles (seed={RANDOM_SEED}, 2022–2026 non-editorials).  "
        f"Haiku model (summaries + coding): `{HAIKU_MODEL}` | Ollama model (summaries): `{OLLAMA_SUMMARY_MODEL}`",
        "",
    ]
    for idx, r in enumerate(results, 1):
        lines.append(f"## {idx}. {r['title'] or '[No title]'}")
        lines.append(f"- Year {r['year']} | v{r['volume']}i{r['issue']} art.{r['article_number']}")
        lines.append(f"- Authors: {r['authors']}")
        lines.append("")
        lines.append(f"**Haiku summary:** {r['summary_haiku']}")
        lines.append("")
        lines.append(f"**Ollama summary:** {r['summary_ollama']}")
        lines.append("")
        lines.append("**Dimension coding (Haiku / taxonomy-constrained with glosses):**")
        coding = r["trend_coding"]
        if isinstance(coding, dict) and "raw_response" not in coding:
            for key in (
                "methodology_primary", "unit_of_analysis_primary", "pedagogy_primary",
                "technology_primary", "theory_primary", "ai_llm_involvement_primary",
                "evidence_span", "coding_confidence", "coding_notes",
            ):
                lines.append(f"- {key}: {coding.get(key, '')}")
        else:
            lines.append(f"- _(JSON parse failed)_ {coding.get('raw_response','')[:200]}")
        lines.append("")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON}")


if __name__ == "__main__":
    main()
