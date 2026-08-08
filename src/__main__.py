import argparse

from .ingest import ingest_pdfs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Root directory containing PDFs (defaults to scanning data/raw 2006-2015 and data/raw 2016-2026)",
    )
    args = parser.parse_args()

    if args.root:
        from pathlib import Path
        ingest_pdfs(Path(args.root))
    else:
        ingest_pdfs()


if __name__ == "__main__":
    main()
