import argparse

from .metadata_corrections import apply_metadata_corrections
from .store import load_store, save_store


def main() -> None:
    argparse.ArgumentParser(
        description="Apply manual metadata corrections from data/metadata_corrections.csv to the article store."
    ).parse_args()

    store = load_store()
    touched = apply_metadata_corrections(store)
    save_store(store)
    print("CORRECTIONS_APPLIED", touched)


if __name__ == "__main__":
    main()