from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data-files"


def get_data_file(rel_path: str) -> str:
    return str(DATA_DIR / rel_path)
