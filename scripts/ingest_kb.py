#!/usr/bin/env python
"""Build FAISS + BM25 from data/kb into data/index.

Calls the Foundry `embed` deployment when LLM_PROVIDER=azure_foundry; falls back to the
deterministic offline embedder in fake mode (README §4.3). Run once; publish the
resulting data/index/ as a GitHub Release artifact so no one re-embeds.
"""

from __future__ import annotations

import logging
import sys

from telecom_agent.config.settings import get_settings
from telecom_agent.rag.ingest import ingest


def main() -> int:
    logging.basicConfig(level="INFO", format="%(levelname)s %(name)s %(message)s")
    settings = get_settings()
    print(
        f"ingesting from {settings.kb_dir} -> {settings.index_dir} "
        f"(provider={settings.llm_provider})"
    )
    n = ingest(settings.kb_dir, settings.index_dir, settings)
    print(f"done: {n} chunks indexed at {settings.index_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
