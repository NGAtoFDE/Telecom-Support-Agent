"""Readers for the approved knowledge base: Markdown runbooks/FAQ/policy files and CSV
FAQ exports. A loader yields ``RawDoc``s; chunking happens downstream.

``doc_id`` and ``title`` come from the front-matter-ish first lines or the manifest so
citations are stable and human-recognisable.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class RawDoc:
    doc_id: str
    title: str
    text: str
    source_path: str


def load_manifest(kb_dir: Path) -> dict[str, dict]:
    """Read ``manifest.yaml`` mapping doc_id -> metadata (title, owner, version, date)."""
    path = kb_dir / "manifest.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    docs = data.get("documents", data)
    return {d["doc_id"]: d for d in docs} if isinstance(docs, list) else docs


def _parse_md(path: Path, manifest: dict[str, dict]) -> RawDoc:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    doc_id = ""
    title = path.stem
    body_start = 0
    # Convention: first two lines may be "doc_id: KB-XXX" and "# Title".
    for i, line in enumerate(lines[:4]):
        if line.lower().startswith("doc_id:"):
            doc_id = line.split(":", 1)[1].strip()
            body_start = i + 1
        elif line.startswith("# "):
            title = line[2:].strip()
            body_start = max(body_start, i + 1)
    if not doc_id:
        doc_id = path.stem.upper()
    meta = manifest.get(doc_id, {})
    title = meta.get("title", title)
    return RawDoc(
        doc_id=doc_id,
        title=title,
        text="\n".join(lines[body_start:]).strip() or text,
        source_path=str(path),
    )


def _parse_csv(path: Path) -> list[RawDoc]:
    docs: list[RawDoc] = []
    with path.open(encoding="utf-8", newline="") as fh:
        for i, row in enumerate(csv.DictReader(fh), start=1):
            q = row.get("question", "").strip()
            a = row.get("answer", "").strip()
            if not (q or a):
                continue
            doc_id = row.get("doc_id") or f"{path.stem.upper()}-{i}"
            docs.append(
                RawDoc(
                    doc_id=doc_id,
                    title=q[:80] or doc_id,
                    text=f"# {q}\n{a}",
                    source_path=str(path),
                )
            )
    return docs


def load_kb(kb_dir: str | Path) -> list[RawDoc]:
    """Walk ``kb_dir`` and load every .md and .csv file into RawDocs."""
    kb_dir = Path(kb_dir)
    manifest = load_manifest(kb_dir)
    docs: list[RawDoc] = []
    for path in sorted(kb_dir.rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        docs.append(_parse_md(path, manifest))
    for path in sorted(kb_dir.rglob("*.csv")):
        docs.extend(_parse_csv(path))
    return docs
