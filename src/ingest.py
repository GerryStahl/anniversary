import re
from pathlib import Path
from typing import Iterable

import fitz  # pymupdf

from .config import RAW_PDF_DIR
from .models import Article
from .store import load_store, save_store, upsert_article


def discover_pdf_files(root: Path = RAW_PDF_DIR) -> Iterable[Path]:
    """
    Yield all PDF files under the given root directory (recursive).
    """
    return root.rglob("*.pdf")


def make_article_id(pdf_path: Path) -> str:
    """
    Create a stable article id from the filename, e.g. "2006-1-2-03".
    You can adjust this to match ijCSCL naming conventions.
    """
    stem = pdf_path.stem  # no extension
    # Example: assume filename encodes year-volume-issue-articleNumber
    # e.g., "2006-1-2-03.pdf"
    return stem


def extract_text_from_pdf(pdf_path: Path) -> tuple[str, list[dict]]:
    """
    Extract full text from a PDF using pymupdf.
    Also returns first page line data with font size information.
    Returns (full_text, first_page_lines)
    """
    doc = fitz.open(pdf_path)
    texts = []
    first_page_lines = []

    for page_idx, page in enumerate(doc):
        texts.append(page.get_text())
        if page_idx == 0:
            page_dict = page.get_text("dict")
            for block in page_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    line_text = "".join(
                        span.get("text", "") for span in line.get("spans", [])
                    ).strip()
                    if not line_text:
                        continue
                    span_text_len = sum(len(span.get("text", "")) for span in line.get("spans", []))
                    if span_text_len == 0:
                        continue
                    avg_size = (
                        sum(
                            span.get("size", 0) * len(span.get("text", ""))
                            for span in line.get("spans", [])
                        )
                        / span_text_len
                    )
                    first_page_lines.append({
                        "text": line_text,
                        "size": avg_size,
                        "bbox": line.get("bbox", []),
                    })

    doc.close()
    return "\n".join(texts), first_page_lines


def extract_basic_metadata_from_pdf(
    pdf_path: Path,
    text: str,
    blocks: list = None,
) -> dict:
    """
    Extract title, authors, year, volume, issue, article_number, doi
    from the file name and/or first page text with font analysis.

    Return a dict with any fields found; others can remain None.
    """
    metadata: dict = {
        "title": None,
        "authors": None,
        "year": None,
        "volume": None,
        "issue": None,
        "article_number": None,
        "doi": None,
    }

    # 1. Parse filename pattern: ijCSCL_volume_issue_article_number
    stem = pdf_path.stem
    parts = stem.split("_")
    if len(parts) >= 4 and parts[0] == "ijCSCL":
        try:
            volume = int(parts[1])
            issue = int(parts[2])
            article_number = int(parts[3])
            metadata["volume"] = volume
            metadata["issue"] = issue
            metadata["article_number"] = article_number
            # Calculate year: 2005 + volume
            metadata["year"] = 2005 + volume
        except (ValueError, IndexError):
            pass

    # Special handling for editorials (article_number=0)
    if metadata.get("article_number") == 0:
        metadata["authors"] = "Gerry Stahl & Friedrich Hesse"

    # 2. Use font-size-aware line classification for title/author extraction
    title_lines = []
    author_lines = []

    if blocks:
        def clean_title_text(t: str) -> str:
            # Special: if book review, extract just the review title
            if t.lower().startswith("book review"):
                match = re.search(r"^(Book review:[^\n]*?)(?:/|\s+[A-Z][a-z]+\s+[A-Z][a-z]+|$)", t)
                if match:
                    return match.group(1).strip()
            # Remove common publication boilerplate and DOIs
            markers = [
                r"Published online:.*$",
                r"/ Published online:.*$",
                r"Received:.*$",
                r"/ Received:.*$",
                r"Accepted:.*$",
                r"/ Accepted:.*$",
                r"Revised:.*$",
                r"/ Revised:.*$",
                r"DOI .*",
                r"/ DOI.*",
                r"Computer-Supported Collaborative Learning.*",
                r"International Society of the Learning Sciences.*",
                r"Springer.*",
                r"\(\d{4}\)\s*\d+:.*",
            ]
            s = t
            for pat in markers:
                s = re.sub(pat, "", s, flags=re.IGNORECASE)
            s = s.strip()
            s = re.sub(r"^\s*[/·•]\s*", "", s)
            s = re.sub(r"\s+/\s*$", "", s)
            parts = [p.strip() for p in re.split(r"[,;\n]", s) if p.strip()]
            if len(parts) >= 2 and parts[0].lower() in parts[1].lower():
                return parts[0]
            s = re.sub(r"\s{2,}", " ", s)
            return s

        def clean_authors_text(a: str, title: str = "") -> str:
            s = a
            # Special: book reviews often have author in subtitle
            if title and "book review" in title.lower():
                name_match = re.search(r"([A-Z][a-z]+(?:\s+[A-Z]\.)?\s+[A-Z][a-z]+)", s)
                if name_match:
                    return name_match.group(1)
                if "," in s:
                    return s.split(",")[0].strip()
            # cut at metadata markers
            cut_markers = [
                "Received:",
                "/Received:",
                "Accepted:",
                "/Accepted:",
                "Revised:",
                "/Revised:",
                "Published",
                "/Published",
                "©",
                "#",
                "doi:",
                "DOI",
            ]
            for m in cut_markers:
                if m in s:
                    s = s.split(m)[0]
            # remove journal/junk mentions
            s = re.sub(r"Computer-Supported Collaborative Learning.*", "", s, flags=re.IGNORECASE)
            s = re.sub(r"International Society of the Learning Sciences.*", "", s, flags=re.IGNORECASE)
            s = re.sub(r"Springer.*", "", s, flags=re.IGNORECASE)
            # Remove leftover fragments
            if "activities in computer supported" in s.lower():
                idx = s.lower().find("activities")
                s = s[:idx].strip()
            s = s.strip()
            s = re.sub(r"^[/·•\s]+", "", s)
            s = re.sub(r"[/·•\s]+$", "", s)
            # If authors contain title fragment, remove that fragment
            if title and title.lower() in s.lower():
                idx = s.lower().find(title.lower())
                if idx >= 0:
                    before = s[:idx].strip()
                    after = s[idx + len(title):].strip()
                    s = (before + " " + after).strip()
            # collapse repeated phrases
            first_part = s.split(",")[0].strip() if "," in s else ""
            if first_part and s.count(first_part) > 1:
                s = s.split(",")[0]
            return s

        def looks_like_author_line(text: str) -> bool:
            if " & " in text or " and " in text:
                return True
            if any(
                token.lower() in text.lower()
                for token in ["university", "college", "school", "lab", "department"]
            ):
                return False
            name_patterns = [
                r"[A-Z][a-z]+ [A-Z][a-z]+",
                r"[A-Z][a-z]+ & [A-Z][a-z]+",
            ]
            if any(re.search(pattern, text) for pattern in name_patterns):
                return True
            comma_parts = [part.strip() for part in text.split(",") if part.strip()]
            if len(comma_parts) >= 2 and all(part and part[0].isupper() for part in comma_parts[:2]):
                return True
            return False

        def is_metadata_line(text: str) -> bool:
            markers = [
                "©",
                "Published",
                "Received",
                "Accepted",
                "doi:",
                "doi.",
                "http",
                "#",
            ]
            return any(marker in text for marker in markers)

        sanitized_lines = [
            line for line in blocks
            if line.get("text") and line.get("size") and len(line.get("text")) > 2
        ]

        if sanitized_lines:
            sizes = sorted(
                {round(line["size"], 1) for line in sanitized_lines},
                reverse=True,
            )
            title_size = sizes[0]
            author_size = sizes[1] if len(sizes) > 1 else title_size
            title_threshold = title_size * 0.92
            author_threshold = author_size * 0.92

            stage = "title"
            for line in sanitized_lines:
                text_line = line["text"].strip()
                line_size = round(line["size"], 1)

                if stage == "title":
                    if line_size >= title_threshold or not looks_like_author_line(text_line):
                        title_lines.append(text_line)
                        continue
                    stage = "authors"

                if stage == "authors":
                    if line_size >= author_threshold and not is_metadata_line(text_line):
                        author_lines.append(text_line)
                        continue
                    stage = "metadata"

                if stage == "metadata":
                    break

        if title_lines:
            raw_title = " ".join(title_lines)
            metadata["title"] = clean_title_text(raw_title.rstrip(",").strip())

        if author_lines:
            raw_authors = " ".join(author_lines)
            metadata["authors"] = clean_authors_text(raw_authors.rstrip(",").strip(), metadata.get("title") or "")
    else:
        first_page_text = text.split("\f")[0] if "\f" in text else text
        lines = [ln.strip() for ln in first_page_text.splitlines() if ln.strip()]

        if len(lines) >= 1:
            raw_title = lines[0].rstrip(",").strip()
            metadata["title"] = clean_title_text(raw_title)
            author_candidates = []
            for line in lines[1:5]:
                if any(marker in line for marker in ["©", "doi:", "Received", "Accepted"]):
                    break
                author_candidates.append(line)
            if author_candidates:
                raw_auth = " ".join(author_candidates).rstrip(",").strip()
                metadata["authors"] = clean_authors_text(raw_auth, metadata.get("title") or "")

    # TODO: add DOI parsing as needed

    return metadata


def ingest_pdfs(root: Path = RAW_PDF_DIR) -> None:
    """
    Main ingestion entrypoint:
    - loads existing store
    - discovers all PDFs
    - extracts text + basic metadata
    - upserts Article records
    - saves store (PKL + JSON)
    """
    store = load_store()

    pdf_paths = list(discover_pdf_files(root))
    for pdf_path in pdf_paths:
        article_id = make_article_id(pdf_path)

        existing = store.get(article_id)
        if existing is not None and existing.fulltext:
            text = existing.fulltext  # Reuse existing text
            _, blocks = extract_text_from_pdf(pdf_path)
        else:
            text, blocks = extract_text_from_pdf(pdf_path)

        basic_meta = extract_basic_metadata_from_pdf(pdf_path, text, blocks)

        article = existing or Article(
            id=article_id,
            filename=pdf_path.name,
            pdf_path=str(pdf_path),
        )

        # Fill/update fields
        article.fulltext = text
        if basic_meta.get("title") is not None:
            article.title = basic_meta["title"]
        if basic_meta.get("authors") is not None:
            article.authors = basic_meta["authors"]
        if basic_meta.get("year") is not None:
            article.year = basic_meta["year"]
        if basic_meta.get("volume") is not None:
            article.volume = basic_meta["volume"]
        if basic_meta.get("issue") is not None:
            article.issue = basic_meta["issue"]
        if basic_meta.get("article_number") is not None:
            article.article_number = basic_meta["article_number"]
        if basic_meta.get("doi") is not None:
            article.doi = basic_meta["doi"]

        upsert_article(store, article)

    save_store(store)
