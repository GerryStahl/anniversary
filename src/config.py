from pathlib import Path

DATA_DIR = Path("data")
RAW_PDF_DIRS = (
	DATA_DIR / "raw 2006-2015",
	DATA_DIR / "raw 2016-2026",
)
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
METADATA_CORRECTIONS_PATH = DATA_DIR / "metadata_corrections.csv"

PKL_PATH = PROCESSED_DIR / "ijcscl.pkl"
JSON_PATH = PROCESSED_DIR / "ijcscl.json"
