from __future__ import annotations

import json
from pathlib import Path

from engine.models import BIAProject

DATA_DIR = Path("data")
DEFAULT_FILE = DATA_DIR / "project.json"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_project(project: BIAProject, path: Path = DEFAULT_FILE) -> Path:
    ensure_data_dir()
    with path.open("w", encoding="utf-8") as f:
        json.dump(project.to_dict(), f, indent=2)
    return path


def load_project(path: Path = DEFAULT_FILE) -> BIAProject:
    ensure_data_dir()
    if not path.exists():
        return BIAProject()

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return BIAProject.from_dict(payload)
