"""Section-aware chunking preserves headings (which become citation sections)."""

from __future__ import annotations

from telecom_agent.rag.chunking import chunk_doc
from telecom_agent.rag.loaders import RawDoc


def _doc() -> RawDoc:
    text = (
        "## Overview\nThis explains the APN reset procedure for Android devices.\n"
        "## Steps\nOpen settings, reset the access point name to default, reboot.\n"
    )
    return RawDoc(doc_id="KB-101", title="APN reset", text=text, source_path="mem")


def test_chunk_doc_preserves_sections():
    chunks = chunk_doc(_doc())
    assert len(chunks) >= 2
    sections = {c.section for c in chunks}
    assert "Overview" in sections
    assert "Steps" in sections
    assert all(c.doc_id == "KB-101" for c in chunks)
    assert all(c.text for c in chunks)


def test_doc_without_headings_yields_one_chunk():
    doc = RawDoc(doc_id="KB-999", title="flat", text="just a flat blob of text", source_path="mem")
    chunks = chunk_doc(doc)
    assert len(chunks) == 1
    assert chunks[0].section == "1"
