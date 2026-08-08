import csv
from pathlib import Path
from typing import Callable

from .config import METADATA_CORRECTIONS_PATH
from .store import ArticlesStore


SUPPORTED_FIELDS: dict[str, Callable[[str], object]] = {
    "title": lambda value: value,
    "authors": lambda value: value,
    "editorial": lambda value: value,
    "doi": lambda value: value,
    "year": int,
    "volume": int,
    "issue": int,
    "article_number": int,
}


def _parse_value(field: str, raw_value: str) -> object:
    value = raw_value.strip()
    if value == "":
        return None
    if value == "__CLEAR__":
        return None
    parser = SUPPORTED_FIELDS[field]
    return parser(value)


def apply_metadata_corrections(
    store: ArticlesStore,
    corrections_path: Path = METADATA_CORRECTIONS_PATH,
) -> int:
    """
    Apply manual metadata corrections from a CSV overlay.

    Blank cells are ignored. Use `__CLEAR__` to explicitly clear a field.
    Returns the number of articles touched.
    """
    if not corrections_path.exists():
        return 0

    with corrections_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return 0

        missing_required = {"id"} - set(reader.fieldnames)
        if missing_required:
            raise ValueError(
                f"Missing required columns in {corrections_path}: {sorted(missing_required)}"
            )

        unknown_columns = {
            column
            for column in reader.fieldnames
            if column not in {"id", "notes"} and column not in SUPPORTED_FIELDS
        }
        if unknown_columns:
            raise ValueError(
                f"Unsupported correction columns in {corrections_path}: {sorted(unknown_columns)}"
            )

        touched = 0
        for row in reader:
            article_id = (row.get("id") or "").strip()
            if not article_id:
                continue
            if article_id not in store:
                raise KeyError(f"Correction references unknown article id: {article_id}")

            article = store[article_id]
            changed = False
            for field in SUPPORTED_FIELDS:
                raw_value = row.get(field)
                if raw_value is None or raw_value.strip() == "":
                    continue
                parsed_value = _parse_value(field, raw_value)
                if getattr(article, field) != parsed_value:
                    setattr(article, field, parsed_value)
                    changed = True

            if changed:
                touched += 1

        return touched
