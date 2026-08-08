import re
from pathlib import Path
from typing import Iterable

import fitz  # pymupdf

from .config import RAW_PDF_DIRS
from .metadata_corrections import apply_metadata_corrections
from .models import Article
from .store import load_store, save_store, upsert_article


def _normalize_roots(root: Path | Iterable[Path] | None = None) -> list[Path]:
    if root is None:
        candidates = RAW_PDF_DIRS
    elif isinstance(root, Path):
        candidates = (root,)
    else:
        candidates = tuple(Path(candidate) for candidate in root)

    roots: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen or not candidate.exists():
            continue
        seen.add(resolved)
        roots.append(candidate)
    return roots


def discover_pdf_files(root: Path | Iterable[Path] | None = None) -> Iterable[Path]:
    """
    Yield all PDF files under one or more root directories (recursive).
    """
    seen: set[Path] = set()
    for pdf_root in _normalize_roots(root):
        for pdf_path in pdf_root.rglob("*.pdf"):
            resolved = pdf_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield pdf_path


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

    def clean_title_text(t: str) -> str:
        # Special: if book review, extract just the review title
        if t.lower().startswith("book review"):
            match = re.search(r"^(Book review:[^\n]*?)(?:/|\s+[A-Z][a-z]+\s+[A-Z][a-z]+|$)", t)
            if match:
                return match.group(1).strip()

        s = t
        # Remove URLs inline first
        s = re.sub(r"https?://\S+", "", s, flags=re.IGNORECASE)

        # Remove common publication boilerplate and DOI / volume metadata
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
            r"\bVol\.?\s*\d+.*$",
            r"\bNo\.?\s*\d+.*$",
            r"\bIssue\s*\d+.*$",
        ]
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

    def is_metadata_line(text_line: str) -> bool:
        lowered = text_line.lower()
        if "©" in text_line or "http" in lowered or "#" in text_line:
            return True

        metadata_patterns = [
            r"\bpublished\b",
            r"\breceived\b",
            r"\baccepted\b",
            r"\bdoi[:.]?\b",
            r"\bvol\.?\s*:?\b",
            r"\bvolume\b",
            r"\bissue\b",
            r"\bno\.?\b",
            r"\babstract\b",
        ]
        return any(re.search(pattern, lowered) for pattern in metadata_patterns)

    def is_header_or_footer_line(text_line: str, y0: float | None, size: float | None) -> bool:
        lowered = text_line.lower().strip()
        if lowered in {"1 3", "13", "1·3"}:
            return True
        if y0 is not None and y0 < 70 and size is not None and size <= 10.5:
            return True
        if "intern. j. comput.-support. collab. learn" in lowered:
            return True
        if lowered.startswith("vol.:(0123456789)"):
            return True
        if lowered.startswith("brief report"):
            return True
        return False

    def normalize_author_chunk(chunk: str) -> str:
        c = re.sub(r"\s+", " ", chunk.strip())
        c = c.replace("\u00a0", " ").replace("\u2009", " ").replace("\u200a", " ")
        c = c.replace("·", " ")
        c = re.sub(r"(?<=\D)\d+(?=\D|$)", "", c)
        c = re.sub(r"^[\W_]+|[\W_]+$", "", c)
        c = re.sub(r"\s{2,}", " ", c).strip()
        return c

    def looks_like_person_name(chunk: str) -> bool:
        lowered = chunk.lower()
        if not chunk:
            return False
        if re.search(r"\d", chunk):
            return False
        forbidden = [
            "university", "college", "department", "school", "faculty", "institute",
            "springer", "computer-supported", "collaborative learning", "http", "doi",
            "published", "received", "accepted", "vol", "volume", "issue", "abstract",
            "keywords", "correspond", "email",
        ]
        if any(token in lowered for token in forbidden):
            return False
        words = chunk.split()
        if len(words) < 2 or len(words) > 8:
            return False

        # Must include at least one likely surname token with initial uppercase
        surname_like = any(
            re.match(r"^[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'`\.\-‑–]+$", w)
            for w in words
        )
        if not surname_like:
            return False

        valid_token = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ'`\.\-‑–]+$|^[A-Z]\.$")
        connector = {"van", "von", "de", "del", "da", "di", "der", "la", "le", "du"}
        for w in words:
            wl = w.lower()
            if wl in connector:
                continue
            if re.match(r"^[A-Z]\.$", w):
                continue
            if not valid_token.match(w):
                return False
        return True

    def extract_author_names(raw: str) -> str:
        s = raw
        s = s.replace("\u00a0", " ").replace("\u2009", " ").replace("\u200a", " ")
        s = re.sub(r"https?://\S+", "", s, flags=re.IGNORECASE)
        s = re.sub(r"[\w.+-]+@[\w.-]+", "", s)
        s = re.sub(r"\bORCID\b.*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s+", " ", s).strip()
        # normalize separators
        s = re.sub(r"\s*[·•]\s*", " & ", s)
        s = re.sub(r"\s+and\s+", " & ", s, flags=re.IGNORECASE)
        s = s.replace(";", " & ")
        s = re.sub(r"(?<=\D)\d+(?=\D|$)", "", s)

        # Split primarily by ampersand; secondarily by commas when needed
        chunks = [normalize_author_chunk(x) for x in re.split(r"\s*&\s*", s) if normalize_author_chunk(x)]
        if len(chunks) <= 1 and "," in s:
            comma_chunks = [normalize_author_chunk(x) for x in s.split(",") if normalize_author_chunk(x)]
            if len(comma_chunks) > 1:
                chunks = comma_chunks

        names = [c for c in chunks if looks_like_person_name(c)]
        if names:
            return " & ".join(names)
        return ""

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
            "Vol.",
            "Volume",
            "Issue",
            "No.",
            "http",
        ]
        for m in cut_markers:
            if m.lower() in s.lower():
                idx = s.lower().find(m.lower())
                s = s[:idx]

        # remove journal/junk mentions
        s = re.sub(r"Computer-Supported Collaborative Learning.*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"International Society of the Learning Sciences.*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"Springer.*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"https?://\S+", "", s, flags=re.IGNORECASE)

        # If authors contain title fragment, remove that fragment
        if title and title.lower() in s.lower():
            idx = s.lower().find(title.lower())
            if idx >= 0:
                before = s[:idx].strip()
                after = s[idx + len(title):].strip()
                s = (before + " " + after).strip()

        extracted = extract_author_names(s)
        return extracted or s.strip()

    def looks_like_author_line(text_line: str) -> bool:
        if is_metadata_line(text_line):
            return False
        if any(
            token.lower() in text_line.lower()
            for token in ["university", "college", "school", "lab", "department", "abstract", "keywords"]
        ):
            return False
        # treat as authors if we can extract at least one valid person name chunk
        return bool(extract_author_names(text_line))

    # 2. Use font-size-aware line classification for title/author extraction
    title_lines = []
    author_lines = []

    if blocks:
        sanitized_lines = [
            line for line in blocks
            if line.get("text") and line.get("size") and len(line.get("text")) > 2
        ]

        if sanitized_lines:
            sanitized_lines = sorted(
                sanitized_lines,
                key=lambda line: (
                    round(line.get("bbox", [0, 0, 0, 0])[1], 1),
                    round(line.get("bbox", [0, 0, 0, 0])[0], 1),
                ),
            )
            def y0(line: dict) -> float:
                return float(line.get("bbox", [0, 0, 0, 0])[1])

            title_zone_lines = [
                line for line in sanitized_lines
                if 70 <= y0(line) <= 220
                and not is_metadata_line(line["text"].strip())
                and not is_header_or_footer_line(line["text"].strip(), y0(line), round(line["size"], 1))
            ]

            size_source = title_zone_lines or sanitized_lines
            sizes = sorted(
                {round(line["size"], 1) for line in size_source},
                reverse=True,
            )
            title_size = sizes[0]
            author_size = sizes[1] if len(sizes) > 1 else title_size
            title_threshold = title_size * 0.92
            author_threshold = author_size * 0.92

            filtered_lines = []
            for line in sanitized_lines:
                text_line = line["text"].strip()
                line_size = round(line["size"], 1)
                if is_metadata_line(text_line):
                    continue
                if is_header_or_footer_line(text_line, y0(line), line_size):
                    continue
                filtered_lines.append(line)

            title_started = False
            title_last_y = None
            author_started = False

            for idx, line in enumerate(filtered_lines):
                text_line = line["text"].strip()
                line_size = round(line["size"], 1)
                line_y0 = y0(line)
                next_gap = None
                if idx + 1 < len(filtered_lines):
                    next_gap = y0(filtered_lines[idx + 1]) - line_y0

                if not title_started:
                    if line_size >= title_threshold and 70 <= line_y0 <= 220:
                        title_started = True
                        title_lines.append(text_line)
                        title_last_y = line_y0
                    continue

                if not author_started:
                    if text_line.lower() == "abstract":
                        break
                    if (
                        looks_like_author_line(text_line)
                        and line_size < title_threshold
                        and line_y0 - (title_last_y or line_y0) >= 8
                    ):
                        author_started = True
                        author_lines.append(text_line)
                        continue
                    if line_size >= title_threshold and (line_y0 - (title_last_y or line_y0)) <= 25:
                        title_lines.append(text_line)
                        title_last_y = line_y0
                        continue
                    if line_y0 > 220 and not author_started:
                        break
                    if next_gap is not None and next_gap > 40:
                        break
                    if line_size < title_threshold and not looks_like_author_line(text_line):
                        break

                else:
                    if text_line.lower() == "abstract" or is_metadata_line(text_line):
                        break
                    if looks_like_author_line(text_line) and line_size >= author_threshold * 0.9:
                        author_lines.append(text_line)
                        continue
                    break

        if title_lines:
            raw_title = " ".join(title_lines)
            metadata["title"] = clean_title_text(raw_title.rstrip(",").strip())

        if author_lines:
            raw_authors = " ".join(author_lines)
            cleaned_authors = clean_authors_text(raw_authors.rstrip(",").strip(), metadata.get("title") or "")
            metadata["authors"] = cleaned_authors or None
    else:
        first_page_text = text.split("\f")[0] if "\f" in text else text
        lines = [ln.strip() for ln in first_page_text.splitlines() if ln.strip()]

        if len(lines) >= 1:
            raw_title = lines[0].rstrip(",").strip()
            metadata["title"] = clean_title_text(raw_title)
            author_candidates = []
            for line in lines[1:5]:
                if is_metadata_line(line):
                    break
                author_candidates.append(line)
            if author_candidates:
                raw_auth = " ".join(author_candidates).rstrip(",").strip()
                cleaned_authors = clean_authors_text(raw_auth, metadata.get("title") or "")
                metadata["authors"] = cleaned_authors or None

    # TODO: add DOI parsing as needed

    return metadata


def ingest_pdfs(root: Path | Iterable[Path] | None = None) -> None:
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

    corrections_applied = apply_metadata_corrections(store)
    if corrections_applied:
        print("CORRECTIONS_APPLIED", corrections_applied)

    save_store(store)
