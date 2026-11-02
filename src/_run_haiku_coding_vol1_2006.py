import json
import os
from pathlib import Path

from anthropic import Anthropic

from src.dimension_taxonomy import TAXONOMY
from src.store import load_store, save_store

HAIKU_MODEL = "claude-haiku-4-5"
OUT_JSON = Path("reports/vol1_2006_dimension_coding.json")


def build_system_prompt() -> str:
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
    dims = "\n".join(blocks)
    return f"""You are an expert in computer-supported collaborative learning (CSCL) and systematic literature review.
Return a compact JSON object with exactly these keys and controlled values:

{dims}
  evidence_span: short phrase indicating which sections support the coding, e.g. \"methods+findings\"
  coding_confidence: a decimal between 0.0 and 1.0
  coding_notes: one or two sentences noting rationale or uncertainty

Rules:
- You MUST choose values from the listed options for each *_primary field. Do not invent labels.
- If no option fits well, choose \"other\" and explain in coding_notes.
- Return only valid JSON. No markdown fences, no extra text outside the JSON object."""


def build_user_prompt(article) -> str:
    snippet = (article.fulltext or "")[:12000]
    if isinstance(article.authors, list):
        authors = " & ".join(str(x) for x in article.authors if str(x).strip())
    else:
        authors = str(article.authors or "Unknown")
    return f"""Title: {article.title or ''}
Authors: {authors}
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
    i = cleaned.find("{")
    j = cleaned.rfind("}")
    if i != -1 and j > i:
        cleaned = cleaned[i : j + 1]
    return json.loads(cleaned)


def main() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set")

    client = Anthropic(api_key=api_key)
    store = load_store()

    targets = [
        article
        for article in store.values()
        if article.year == 2006 and article.volume == 1 and (article.fulltext or "").strip()
    ]
    targets.sort(
        key=lambda a: (
            a.issue if isinstance(a.issue, int) else 999,
            a.article_number if isinstance(a.article_number, int) else 999,
            a.id,
        )
    )

    print("TARGETS", len(targets))

    system_prompt = build_system_prompt()
    results = []
    updated = 0

    for idx, article in enumerate(targets, 1):
        print(f"[{idx}/{len(targets)}] {article.id}")
        response = client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=600,
            temperature=0.2,
            system=system_prompt,
            messages=[{"role": "user", "content": build_user_prompt(article)}],
        )
        raw = " ".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )

        try:
            coding = extract_json(raw)
        except Exception:
            coding = {"raw_response": raw}

        if "raw_response" not in coding:
            before = (
                article.methodology_primary,
                article.unit_of_analysis_primary,
                article.pedagogy_primary,
                article.technology_primary,
                article.theory_primary,
                article.ai_llm_involvement_primary,
                article.evidence_span,
                article.coding_confidence,
                article.coding_notes,
            )

            article.methodology_primary = coding.get("methodology_primary")
            article.unit_of_analysis_primary = coding.get("unit_of_analysis_primary")
            article.pedagogy_primary = coding.get("pedagogy_primary")
            article.technology_primary = coding.get("technology_primary")
            article.theory_primary = coding.get("theory_primary")
            article.ai_llm_involvement_primary = coding.get("ai_llm_involvement_primary")
            article.evidence_span = coding.get("evidence_span")
            article.coding_confidence = coding.get("coding_confidence")
            article.coding_notes = coding.get("coding_notes")

            after = (
                article.methodology_primary,
                article.unit_of_analysis_primary,
                article.pedagogy_primary,
                article.technology_primary,
                article.theory_primary,
                article.ai_llm_involvement_primary,
                article.evidence_span,
                article.coding_confidence,
                article.coding_notes,
            )
            if before != after:
                updated += 1

        results.append(
            {
                "id": article.id,
                "year": article.year,
                "volume": article.volume,
                "issue": article.issue,
                "article_number": article.article_number,
                "editorial": article.editorial,
                "title": article.title,
                "coding": coding,
            }
        )

    save_store(store)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print("UPDATED", updated)
    print("REPORT", OUT_JSON)


if __name__ == "__main__":
    main()
