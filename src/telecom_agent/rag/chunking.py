"""Section-aware Markdown splitter.

Splits on Markdown headings so each chunk keeps the heading it belongs to — that heading
becomes the ``section`` in the citation, which is what makes "[KB-114 §2.3]" possible.
Oversized sections are further split on a token budget with a small overlap.
"""

from __future__ import annotations

import re

from telecom_agent.core.types import Chunk
from telecom_agent.core.utils import approx_tokens, normalize_text
from telecom_agent.rag.loaders import RawDoc

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def _sections(text: str) -> list[tuple[str, str]]:
    """Return (section_label, body) pairs. Section labels are hierarchical, e.g. '2.3'
    is approximated by the heading text; we keep the heading string as the section id."""
    sections: list[tuple[str, str]] = []
    current_label = "1"
    buf: list[str] = []
    counter = 0
    for line in text.splitlines():
        m = _HEADING.match(line)
        if m:
            if buf:
                sections.append((current_label, "\n".join(buf).strip()))
                buf = []
            counter += 1
            heading_text = m.group(2).strip()
            current_label = heading_text or str(counter)
        else:
            buf.append(line)
    if buf:
        sections.append((current_label, "\n".join(buf).strip()))
    return [(lbl, body) for lbl, body in sections if body]


def _split_long(body: str, max_tokens: int, overlap: int) -> list[str]:
    if approx_tokens(body) <= max_tokens:
        return [body]
    words = body.split()
    window = max(50, max_tokens)  # words per window (approx token≈word for prose)
    step = max(1, window - overlap)
    out = []
    for start in range(0, len(words), step):
        out.append(" ".join(words[start : start + window]))
        if start + window >= len(words):
            break
    return out


def chunk_doc(doc: RawDoc, *, max_tokens: int = 220, overlap: int = 30) -> list[Chunk]:
    chunks: list[Chunk] = []
    for label, body in _sections(doc.text):
        for piece in _split_long(body, max_tokens, overlap):
            chunks.append(
                Chunk(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    section=label,
                    text=normalize_text(piece),
                )
            )
    if not chunks:  # a doc with no headings still yields one chunk
        chunks.append(
            Chunk(doc_id=doc.doc_id, title=doc.title, section="1", text=normalize_text(doc.text))
        )
    return chunks


def chunk_docs(docs: list[RawDoc], **kw: int) -> list[Chunk]:
    out: list[Chunk] = []
    for doc in docs:
        out.extend(chunk_doc(doc, **kw))
    return out
