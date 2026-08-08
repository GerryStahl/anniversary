from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class Article:
    id: str                    # stable identifier, e.g. "2006-1-2-03"
    filename: str
    pdf_path: str

    title: Optional[str] = None
    authors: Optional[List[str]] = None
    year: Optional[int] = None
    volume: Optional[int] = None
    issue: Optional[int] = None
    article_number: Optional[int] = None
    doi: Optional[str] = None

    fulltext: Optional[str] = None

    summary_ollama: Optional[str] = None
    summary_haiku: Optional[str] = None
    category: Optional[str] = None   # "a".."f" later
    editorial: Optional[str] = None

    # Dimension coding for trend analysis (interpretability-first, evidence-based)
    methodology_primary: Optional[str] = None
    methodology_secondary: Optional[List[str]] = None
    unit_of_analysis_primary: Optional[str] = None
    unit_of_analysis_secondary: Optional[List[str]] = None
    pedagogy_primary: Optional[str] = None
    pedagogy_secondary: Optional[List[str]] = None
    technology_primary: Optional[str] = None
    technology_secondary: Optional[List[str]] = None
    theory_primary: Optional[str] = None
    theory_secondary: Optional[List[str]] = None
    ai_llm_involvement_primary: Optional[str] = None
    ai_llm_involvement_secondary: Optional[List[str]] = None

    # Coding metadata
    evidence_span: Optional[str] = None
    coding_confidence: Optional[float] = None
    extends_methodology: Optional[bool] = None
    extends_pedagogy: Optional[bool] = None
    extends_technology: Optional[bool] = None
    extends_theory: Optional[bool] = None
    coding_notes: Optional[str] = None

    embedding_ollama_summary: Optional[List[float]] = None
    embedding_haiku_summary: Optional[List[float]] = None
    embedding_fulltext: Optional[List[float]] = None

    cluster_ollama_summary: Optional[int] = None
    cluster_haiku_summary: Optional[int] = None
    cluster_fulltext: Optional[int] = None

    embedding_model: Optional[str] = None
    embedding: Optional[List[float]] = None

    EMBEDDING_FIELDS = (
        "embedding_ollama_summary",
        "embedding_haiku_summary",
        "embedding_fulltext",
        "embedding",
    )

    def to_dict(self, include_text: bool = True, include_embeddings: bool = True) -> dict:
        d = asdict(self)
        if not include_text:
            d.pop("fulltext", None)
        if not include_embeddings:
            for field in self.EMBEDDING_FIELDS:
                if field in d:
                    d[field] = "embedded" if d[field] is not None else None
        return d

    @property
    def text(self) -> Optional[str]:
        return self.fulltext

    @text.setter
    def text(self, value: Optional[str]) -> None:
        self.fulltext = value

    @property
    def ollama_summary(self) -> Optional[str]:
        return self.summary_ollama

    @ollama_summary.setter
    def ollama_summary(self, value: Optional[str]) -> None:
        self.summary_ollama = value

    @property
    def claude_summary(self) -> Optional[str]:
        return self.summary_haiku

    @claude_summary.setter
    def claude_summary(self, value: Optional[str]) -> None:
        self.summary_haiku = value
