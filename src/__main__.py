import argparse

from .ingest import ingest_pdfs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Root directory containing PDFs (defaults to config.RAW_PDF_DIR)",
    )
    args = parser.parse_args()

    if args.root:
        from pathlib import Path
        ingest_pdfs(Path(args.root))
    else:
        ingest_pdfs()


if __name__ == "__main__":
    main()
