import argparse
import subprocess
from pathlib import Path

from src.build_articles_csv import build_articles_csv
from src.build_cluster_haiku_summary_csv import build_cluster_haiku_summary_csv
from src.build_trends_dataset_csv import build_trends_dataset
from src.metadata_corrections import apply_metadata_corrections
from src.store import load_store, save_store


REPO_ROOT = Path(__file__).resolve().parents[1]

TEMP_FILES = [
    "update_field.py",
    "update_category.py",
    "check_csv.py",
    "_regen_cluster_csv.py",
    "recategorize_temp.py",
    "recategorize_with_ollama.py",
]


def run_cmd(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), text=True, capture_output=True, check=False)


def cleanup_temp_files(repo_root: Path) -> list[str]:
    removed = []
    for rel_path in TEMP_FILES:
        file_path = repo_root / rel_path
        if file_path.exists():
            file_path.unlink()
            removed.append(rel_path)
    return removed


def git_commit_and_push(repo_root: Path, commit_message: str, push: bool) -> None:
    add_result = run_cmd(["git", "add", "README.md", "src", "reports", "documentation", "data/metadata_corrections.csv"], cwd=repo_root)
    if add_result.returncode != 0:
        raise RuntimeError(f"git add failed:\n{add_result.stderr}")

    staged_result = run_cmd(["git", "diff", "--cached", "--quiet"], cwd=repo_root)
    if staged_result.returncode == 0:
        print("GIT_STATUS no staged changes to commit")
        return

    commit_result = run_cmd(["git", "commit", "-m", commit_message], cwd=repo_root)
    if commit_result.returncode != 0:
        raise RuntimeError(f"git commit failed:\n{commit_result.stderr}\n{commit_result.stdout}")
    print("GIT_COMMIT ok")

    if push:
        push_result = run_cmd(["git", "push", "origin", "main"], cwd=repo_root)
        if push_result.returncode != 0:
            raise RuntimeError(f"git push failed:\n{push_result.stderr}\n{push_result.stdout}")
        print("GIT_PUSH ok")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="End-of-session refresh: clean temp files, rebuild reports from PKL, and optionally commit/push to GitHub."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Create a git commit with refreshed outputs",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push commit to origin/main (implies --commit)",
    )
    parser.add_argument(
        "--message",
        type=str,
        default="Refresh reports and end-of-session cleanup",
        help="Commit message used when --commit/--push is provided",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip temporary file cleanup",
    )
    args = parser.parse_args()

    if not args.no_clean:
        removed = cleanup_temp_files(REPO_ROOT)
        print("CLEANED", ", ".join(removed) if removed else "none")

    # Persist schema migrations to PKL/JSON mirrors before report generation.
    store = load_store()
    corrections_applied = apply_metadata_corrections(store)
    save_store(store)
    print("STORE_SAVED", "data/processed/ijcscl.pkl", "data/processed/ijcscl.json")
    print("CORRECTIONS_APPLIED", corrections_applied)

    articles_path = build_articles_csv(REPO_ROOT / "reports" / "articles.csv")
    cluster_path = build_cluster_haiku_summary_csv(REPO_ROOT / "reports" / "cluster_haiku_summary.csv")
    trends_path = REPO_ROOT / "reports" / "trends_dataset.csv"
    rows_written, editorials_excluded = build_trends_dataset(trends_path, include_editorials=False)

    print("REPORT", articles_path)
    print("REPORT", cluster_path)
    print("REPORT", trends_path)
    print("TRENDS_ROWS", rows_written)
    print("TRENDS_EDITORIALS_EXCLUDED", editorials_excluded)

    if args.commit or args.push:
        git_commit_and_push(REPO_ROOT, args.message, push=args.push)


if __name__ == "__main__":
    main()
