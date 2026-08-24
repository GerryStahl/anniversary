#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from anthropic import Anthropic
except ImportError as exc:  # pragma: no cover - friendly CLI failure
    raise SystemExit(
        "Missing dependency 'anthropic'. Install with `pip install -r requirements.txt`."
    ) from exc

from src.dimension_taxonomy import TAXONOMY
from src.store import load_store, save_store

DEFAULT_MODEL = "claude-haiku-4-5"
OUTPUT_CSV = Path("reports/trends_dataset.csv")


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
        blocks.append(
            f"  {dim_key}_primary — choose ONE of:\n{dim.prompt_block()}\n"
            f"  {dim_key}_secondary — choose 0 to 2 additional values from the same list, as a JSON array of strings. Keep it brief."
        )

    dims = "\n".join(blocks)

    return f"""You are an expert in computer-supported collaborative learning (CSCL) and systematic literature review.
Return a compact JSON object with exactly these keys and controlled values:

{dims}
  evidence_span: short phrase indicating the sections/materials supporting the coding, e.g. "methods+findings"
  coding_confidence: a decimal between 0.0 and 1.0
  coding_notes: one or two sentences noting rationale or uncertainty

Rules:
- For each *_primary field, choose exactly ONE value from the listed options. Do not invent labels.
- For each *_secondary field, return a JSON array of 0 to 2 values from the same list.
- If no option fits well, choose "other" for the primary and explain in coding_notes.
- Keep secondary values distinct from primary when possible.
- Return only valid JSON. No markdown fences, no extra text outside the JSON object."""


def build_user_prompt(article) -> str:
    snippet = (article.summary_haiku or article.fulltext or "")[:12000]
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

Article summary/excerpt:
{snippet}""".strip()


def extract_json(text: str) -> dict:
    text = text.strip()
    if not text:
        raise ValueError("Empty model output")
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    text = text.strip()
    return json.loads(text)


def normalize_secondary(value):
    if value is None:
        return []
    if isinstance(value, list):
        items = []
        for v in value:
            if isinstance(v, str):
                items.append(v)
        return items[:2]
    if isinstance(value, str):
        raw = [v.strip() for v in value.split(",") if v.strip()]
        return raw[:2]
    return []


def assign_dimensions_for_article(client: Anthropic, article, model: str) -> dict:
    response = client.messages.create(
        model=model,
        max_tokens=500,
        temperature=0.15,
        system=build_system_prompt(),
        messages=[{"role": "user", "content": build_user_prompt(article)}],
    )

    parts = []
    for block in getattr(response, "content", []) or []:
        if getattr(block, "type", None) == "text" and getattr(block, "text", ""):
            parts.append(block.text)

    text = " ".join(parts)
    data = extract_json(text)

    out = {}
    for dim_key in (
        "methodology",
        "unit_of_analysis",
        "pedagogy",
        "technology",
        "theory",
        "ai_llm_involvement",
    ):
        primary_key = f"{dim_key}_primary"
        secondary_key = f"{dim_key}_secondary"
        primary_value = data.get(primary_key)
        if primary_value not in TAXONOMY[dim_key].options:
            primary_value = "other"
        secondary_value = normalize_secondary(data.get(secondary_key))
        secondary_clean = []
        for item in secondary_value:
            if item in TAXONOMY[dim_key].options and item != primary_value:
                secondary_clean.append(item)
        out[primary_key] = primary_value
        out[secondary_key] = secondary_clean[:2]

    out["evidence_span"] = data.get("evidence_span") or "summary"
    out["coding_confidence"] = float(data.get("coding_confidence", 0.5)) if data.get("coding_confidence") is not None else 0.5
    out["coding_notes"] = data.get("coding_notes") or "Assigned from summary_haiku."
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assign primary/secondary dimension codes for all articles using summary_haiku, with full-text fallback only if needed."
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Anthropic model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=25,
        help="Save store every N articles (default: 25)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on number of articles to code",
    )
    return parser.parse_args()


def main() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set.")

    args = parse_args()
    client = Anthropic(api_key=api_key)

    store = load_store()
    article_list = [
        article for article in store.values()
        if (article.summary_haiku or article.fulltext)
    ]
    article_list.sort(
        key=lambda a: (
            a.year if isinstance(a.year, int) else 9999,
            a.volume if isinstance(a.volume, int) else 999,
            a.issue if isinstance(a.issue, int) else 999,
            a.article_number if isinstance(a.article_number, int) else 999,
            a.id,
        )
    )

    if args.limit is not None:
        article_list = article_list[: args.limit]

    n = 0
    checkpoint_count = 0
    for article in article_list:
        n += 1
        if not (article.summary_haiku or article.fulltext):
            continue

        try:
            assignments = assign_dimensions_for_article(client, article, model=args.model)
        except Exception as exc:
            print(f"FAILED {article.id}: {exc}")
            assignments = {
                "methodology_primary": "other",
                "methodology_secondary": [],
                "unit_of_analysis_primary": "other",
                "unit_of_analysis_secondary": [],
                "pedagogy_primary": "other",
                "pedagogy_secondary": [],
                "technology_primary": "other",
                "technology_secondary": [],
                "theory_primary": "other",
                "theory_secondary": [],
                "ai_llm_involvement_primary": "other",
                "ai_llm_involvement_secondary": [],
                "evidence_span": "summary",
                "coding_confidence": 0.25,
                "coding_notes": f"Fallback assignment because the model call failed: {exc}",
            }

        for key, value in assignments.items():
            setattr(article, key, value)

        checkpoint_count += 1
        if checkpoint_count >= args.checkpoint_every:
            save_store(store)
            checkpoint_count = 0
            print(f"SAVED CHECKPOINT after {n} articles")

    save_store(store)
    print(f"DONE: coded {n} article(s)")


if __name__ == "__main__":
    main()
