#!/usr/bin/env python3
"""Download open-access PDFs from Springer journal 11412 (2016-present)."""

from __future__ import annotations

import csv
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests

BASE = "https://link.springer.com"
VOLUMES_URL = f"{BASE}/journal/11412/volumes-and-issues"
MIN_VOLUME = 11  # volume 1 = 2006, so volume 11 = 2016
OUTDIR = Path("/Users/GStahl2/Downloads/e-library_oa_11412_2016_present")
PDF_DIR = OUTDIR / "pdfs"
MANIFEST_PATH = OUTDIR / "manifest_oa_2016_present.csv"
SUMMARY_PATH = OUTDIR / "summary.txt"


session = requests.Session()
session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
        )
    }
)


def fetch_text(url: str, retries: int = 4, timeout: int = 40) -> str | None:
    for i in range(retries):
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.text
        except requests.RequestException:
            pass
        time.sleep(1.2 * (i + 1))
    return None


def fetch_pdf(url: str, retries: int = 4, timeout: int = 60) -> bytes | None:
    for i in range(retries):
        try:
            response = session.get(url, timeout=timeout)
            ctype = (response.headers.get("content-type") or "").lower()
            if response.status_code == 200 and (
                "pdf" in ctype or response.content.startswith(b"%PDF")
            ):
                return response.content
        except requests.RequestException:
            pass
        time.sleep(1.2 * (i + 1))
    return None


def safe_filename_component(value: str, max_len: int = 90) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", value).strip().replace(" ", "_")
    return cleaned[:max_len]


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    volumes_html = fetch_text(VOLUMES_URL)
    if not volumes_html:
        raise RuntimeError("Failed to fetch volumes page")

    issue_matches = set(
        re.findall(r"/journal/11412/volumes-and-issues/(\d+)-(\d+)", volumes_html)
    )
    issues: list[tuple[int, int, str]] = [
        (int(volume), int(issue), f"/journal/11412/volumes-and-issues/{volume}-{issue}")
        for volume, issue in issue_matches
        if int(volume) >= MIN_VOLUME
    ]
    issues.sort(key=lambda x: (x[0], x[1]))

    article_triplets: list[tuple[int, int, str]] = []
    seen_articles: set[str] = set()

    for volume, issue, issue_path in issues:
        issue_html = fetch_text(urljoin(BASE, issue_path))
        if not issue_html:
            continue

        links = re.findall(r'href="(/article/10\.1007/s11412-[^"]+)"', issue_html)
        for link in links:
            article_url = urljoin(BASE, link.split("?")[0])
            if article_url not in seen_articles:
                seen_articles.add(article_url)
                article_triplets.append((volume, issue, article_url))

        time.sleep(0.25)

    rows: list[dict[str, str | int | bool]] = []
    downloaded = 0

    for idx, (volume, issue, article_url) in enumerate(article_triplets, start=1):
        article_html = fetch_text(article_url)
        if not article_html:
            rows.append(
                {
                    "volume": volume,
                    "issue": issue,
                    "year": "",
                    "doi": "",
                    "title": "",
                    "article_url": article_url,
                    "oa": False,
                    "pdf_url": "",
                    "status": "article_fetch_failed",
                    "file": "",
                }
            )
            continue

        doi_match = re.search(r'name="citation_doi" content="([^"]+)"', article_html)
        title_match = re.search(
            r'name="citation_title" content="([^"]+)"', article_html
        )
        year_match = re.search(
            r'name="citation_publication_date" content="(\d{4})', article_html
        )
        pdf_match = re.search(
            r'name="citation_pdf_url" content="([^"]+)"', article_html
        )

        doi = doi_match.group(1).strip() if doi_match else article_url.rsplit("/", 1)[-1]
        title = title_match.group(1).strip() if title_match else ""
        year = year_match.group(1) if year_match else ""
        pdf_url = pdf_match.group(1).strip() if pdf_match else ""

        is_oa = bool(pdf_url)
        status = "not_open_access"
        output_path = ""

        if is_oa:
            safe_doi = doi.replace("/", "_")
            safe_title = safe_filename_component(title)
            filename = f"{year or 'unknown'}_v{volume}i{issue}_{safe_doi}"
            if safe_title:
                filename += f"_{safe_title}"
            filename += ".pdf"
            target = PDF_DIR / filename

            pdf_bytes = fetch_pdf(pdf_url)
            if pdf_bytes:
                target.write_bytes(pdf_bytes)
                status = "downloaded"
                output_path = str(target)
                downloaded += 1
            else:
                status = "pdf_download_failed"

        rows.append(
            {
                "volume": volume,
                "issue": issue,
                "year": year,
                "doi": doi,
                "title": title,
                "article_url": article_url,
                "oa": is_oa,
                "pdf_url": pdf_url,
                "status": status,
                "file": output_path,
            }
        )

        if idx % 20 == 0:
            print(
                f"Processed {idx}/{len(article_triplets)} articles; downloaded={downloaded}"
            )
        time.sleep(0.25)

    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "volume",
                "issue",
                "year",
                "doi",
                "title",
                "article_url",
                "oa",
                "pdf_url",
                "status",
                "file",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    SUMMARY_PATH.write_text(
        "\n".join(
            [
                f"Issues scanned: {len(issues)}",
                f"Articles discovered: {len(article_triplets)}",
                f"Open-access PDFs downloaded: {downloaded}",
                f"Manifest: {MANIFEST_PATH}",
                f"PDF directory: {PDF_DIR}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print("Done")
    print(f"Issues scanned: {len(issues)}")
    print(f"Articles discovered: {len(article_triplets)}")
    print(f"Open-access PDFs downloaded: {downloaded}")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"PDF directory: {PDF_DIR}")


if __name__ == "__main__":
    main()
