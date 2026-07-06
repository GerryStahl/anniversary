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
