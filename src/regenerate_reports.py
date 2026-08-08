#!/usr/bin/env python3
import argparse
from pathlib import Path

from src.config import RAW_PDF_DIRS
from src.ingest import ingest_pdfs


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate article store and report files from raw PDF inputs."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Path to raw PDF directory (defaults to scanning data/raw 2006-2015 and data/raw 2016-2026).",
    )
    args = parser.parse_args()

    root = Path(args.root) if args.root else RAW_PDF_DIRS
    if args.root and not Path(args.root).exists():
        raise SystemExit(f"Raw PDF directory not found: {args.root}")

    if args.root:
        print(f"Regenerating from raw PDFs in: {root}")
    else:
        print("Regenerating from raw PDFs in: " + ", ".join(str(path) for path in RAW_PDF_DIRS))
    ingest_pdfs(root)
    print("Regeneration complete. Updated data/processed/ijcscl.pkl, data/processed/ijcscl.json, and reports/articles.csv.")


if __name__ == "__main__":
    main()
