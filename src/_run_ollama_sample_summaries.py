"""
One-off: generate Ollama summaries for the 5 sample articles and write a
comparison report against any existing Haiku summaries.
Run with: PYTHONPATH=$PWD python src/_run_ollama_sample_summaries.py
"""
import json
import random
from pathlib import Path

from src.llm import ollama_chat
from src.store import load_store
from src.summarize import SUMMARIZATION_SYSTEM_PROMPT, clean_summary

RANDOM_SEED = 42
RECENT_YEARS = {2022, 2023, 2024, 2025, 2026}
MODEL = "llama3.1:8b"
REPORT = Path("reports/recent5yr_sample_ollama_vs_haiku.md")


def format_authors(article) -> str:
    if isinstance(article.authors, list):
        return " & ".join(str(x) for x in article.authors if str(x).strip())
    return str(article.authors or "Unknown")


def build_user_prompt(article) -> str:
    snippet = (article.fulltext or "")[:12000]
    return f"""Title: {article.title or ''}
Authors: {format_authors(article)}
Year: {article.year or ''}
Article ID: {article.id}

Article excerpt:
{snippet}""".strip()


def main() -> None:
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
        print(f"[{idx}/5] Summarising: {a.title or a.id[:70]}")
        summary = clean_summary(
            ollama_chat(
                model=MODEL,
                system_prompt=SUMMARIZATION_SYSTEM_PROMPT,
                user_prompt=build_user_prompt(a),
                temperature=0.2,
            )
        )
        results.append({
            "id": a.id,
            "year": a.year,
            "volume": a.volume,
            "issue": a.issue,
            "article_number": a.article_number,
            "title": a.title,
            "authors": format_authors(a),
            "summary_ollama": summary,
            "summary_haiku": a.summary_haiku or "(none yet)",
        })
        print(f"       {summary[:100]}...")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Sample review: Ollama vs Haiku summaries",
        "",
        f"Same 5 articles as the trend-coding sample (seed={RANDOM_SEED}, 2022–2026 non-editorials).",
        f"Ollama model: `{MODEL}`  |  Haiku model: `claude-haiku-4-5`",
        "",
    ]
    for idx, r in enumerate(results, 1):
        lines.append(f"## {idx}. {r['title'] or '[No title]'}")
        lines.append(f"- Year {r['year']} | v{r['volume']}i{r['issue']} art.{r['article_number']}")
        lines.append(f"- Authors: {r['authors']}")
        lines.append(f"- **Ollama (`{MODEL}`):** {r['summary_ollama']}")
        lines.append(f"- **Haiku (`claude-haiku-4-5`):** {r['summary_haiku']}")
        lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {REPORT}")

    print("\n=== SIDE-BY-SIDE ===")
    for r in results:
        print(f"\n--- {r['id'][:80]}")
        print(f"OLLAMA : {r['summary_ollama']}")
        print(f"HAIKU  : {r['summary_haiku']}")


if __name__ == "__main__":
    main()
