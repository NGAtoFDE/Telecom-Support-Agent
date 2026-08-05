"""Small shared helpers for datasets and reports (kept out of ``metrics.py`` so those stay
pure functions). Not a runner itself."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).parent
DATASETS_DIR = _ROOT / "datasets"
REPORTS_DIR = _ROOT / "reports"
BASELINES_DIR = _ROOT / "baselines"


def load_jsonl(name: str) -> list[dict]:
    """Load a dataset by filename (with or without .jsonl) from evals/datasets."""
    if not name.endswith(".jsonl"):
        name += ".jsonl"
    path = DATASETS_DIR / name
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            rows.append(json.loads(line))
    return rows


def write_report(name: str, markdown: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if not name.endswith(".md"):
        name += ".md"
    path = REPORTS_DIR / name
    path.write_text(markdown, encoding="utf-8")
    return path


def load_baseline(provider: str) -> dict:
    path = BASELINES_DIR / f"{provider}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
