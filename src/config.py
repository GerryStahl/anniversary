from pathlib import Path

DATA_DIR = Path("data")
RAW_PDF_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

PKL_PATH = PROCESSED_DIR / "ijcscl.pkl"
JSON_PATH = PROCESSED_DIR / "ijcscl.json"
