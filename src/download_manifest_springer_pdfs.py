#!/usr/bin/env python3
"""Download Springer PDFs listed in a manifest using an interactive Playwright browser session.

Usage:
  PYTHONPATH=$PWD python -m src.download_manifest_springer_pdfs \
    --manifest documentation/manifest_oa_2016_present_not_downloaded.csv \
    --outdir "data/raw 2016-2026"
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
import time
from pathlib import Path

from playwright.sync_api import BrowserContext
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


def safe_filename_component(value: str, max_len: int = 120) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", value).strip().replace(" ", "_")
    return cleaned[:max_len]


def build_filename(row: dict[str, str]) -> str:
    year = (row.get("year") or "unknown").strip()
    volume = (row.get("volume") or "").strip()
    issue = (row.get("issue") or "").strip()
    doi = (row.get("doi") or "").strip().replace("/", "_")
    title = safe_filename_component((row.get("title") or "").strip())

    base = f"{year}_v{volume}i{issue}_{doi}"
    if title:
        base += f"_{title}"
    return base + ".pdf"


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def try_download_one(
    context: BrowserContext,
    row: dict[str, str],
    outdir: Path,
    timeout_ms: int = 90000,
) -> tuple[bool, str]:
    article_url = (row.get("article_url") or "").strip()
    pdf_url = (row.get("pdf_url") or "").strip()
    target = outdir / build_filename(row)

    if target.exists() and target.stat().st_size > 0:
        return True, "exists"

    page = context.new_page()
    try:
        # Strategy A: direct PDF URL
        if pdf_url:
            try:
                with page.expect_download(timeout=timeout_ms) as dli:
                    page.goto(pdf_url, wait_until="domcontentloaded", timeout=timeout_ms)
                dl = dli.value
                tmp = dl.path()
                if tmp:
                    shutil.copy(tmp, target)
                    return True, "downloaded_via_pdf_url"
            except Exception:
                pass

        try:
            page.goto(article_url, wait_until="domcontentloaded", timeout=timeout_ms)
        except Exception as e:
            return False, f"article_load_failed: {e}"

        selectors = [
            "a[data-test='download-pdf-link']",
            "a[title='Download this article in PDF format']",
            "a:has-text('Download PDF')",
            "a[href*='/content/pdf/']",
            "a[href*='epdf']",
        ]

        for sel in selectors:
            try:
                locator = page.locator(sel).first
                if locator.count() == 0:
                    continue
                with page.expect_download(timeout=timeout_ms) as dli:
                    locator.click()
                dl = dli.value
                tmp = dl.path()
                if tmp:
                    shutil.copy(tmp, target)
                    return True, f"downloaded_via_click:{sel}"
            except Exception:
                continue

        href_candidates = page.eval_on_selector_all(
            "a",
            "els => els.map(e => e.href).filter(h => h && (h.includes('/content/pdf/') || h.includes('epdf')))",
        )
        for href in href_candidates[:5]:
            try:
                with page.expect_download(timeout=timeout_ms) as dli:
                    page.goto(href, wait_until="domcontentloaded", timeout=timeout_ms)
                dl = dli.value
                tmp = dl.path()
                if tmp:
                    shutil.copy(tmp, target)
                    return True, "downloaded_via_href"
            except Exception:
                continue

        return False, "download_not_triggered"
    finally:
        try:
            page.close()
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("documentation/manifest_oa_2016_present_not_downloaded.csv"),
    )
    parser.add_argument("--outdir", type=Path, default=Path("data/raw 2016-2026"))
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--resume-log",
        type=Path,
        default=Path("reports/manifest_download_log.csv"),
    )
    args = parser.parse_args()

    rows = read_manifest(args.manifest)
    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    args.outdir.mkdir(parents=True, exist_ok=True)
    args.resume_log.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # Manual-auth checkpoint.
        auth_page = context.new_page()
        auth_page.goto("https://link.springer.com", wait_until="domcontentloaded", timeout=120000)
        print("\nIf needed, log in to Springer in the opened browser window now.")
        print("After login, press ENTER here to start downloads...", flush=True)
        input()
        try:
            auth_page.close()
        except Exception:
            pass

        downloaded = 0
        skipped = 0
        failed = 0

        with args.resume_log.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["doi", "year", "volume", "issue", "status", "detail", "file"])

            total = len(rows)
            for i, row in enumerate(rows, start=1):
                doi = (row.get("doi") or "").strip()
                file_path = str(args.outdir / build_filename(row))
                try:
                    ok, detail = try_download_one(context, row, args.outdir)
                except PlaywrightTimeoutError:
                    ok, detail = False, "timeout"
                except Exception as e:
                    ok, detail = False, f"error:{e}"

                if ok and detail == "exists":
                    skipped += 1
                    status = "skipped"
                elif ok:
                    downloaded += 1
                    status = "downloaded"
                else:
                    failed += 1
                    status = "failed"

                w.writerow(
                    [
                        doi,
                        row.get("year", ""),
                        row.get("volume", ""),
                        row.get("issue", ""),
                        status,
                        detail,
                        file_path,
                    ]
                )
                f.flush()

                print(f"[{i}/{total}] {doi} -> {status} ({detail})")
                time.sleep(0.2)

        context.close()
        browser.close()

    print("\nDone")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped:    {skipped}")
    print(f"Failed:     {failed}")
    print(f"Log:        {args.resume_log}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
