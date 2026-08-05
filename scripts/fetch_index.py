#!/usr/bin/env python
"""Download the published FAISS + BM25 index from a GitHub Release artifact.

The built index is published as a release artifact so no teammate and no container ever
re-embeds (README §4.3). Point INDEX_RELEASE_URL at the artifact (a .zip or .tar.gz of the
index_dir contents). If it is unset this is a friendly no-op — run `make ingest` instead.
"""

from __future__ import annotations

import os
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from telecom_agent.config.settings import get_settings


def main() -> int:
    url = os.getenv("INDEX_RELEASE_URL", "").strip()
    index_dir = Path(get_settings().index_dir)

    if not url:
        print("INDEX_RELEASE_URL is not set.")
        print("Either set it to a published release artifact URL, or build locally:")
        print("    make ingest")
        return 0

    index_dir.mkdir(parents=True, exist_ok=True)
    print(f"downloading index artifact from {url}")
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        urllib.request.urlretrieve(url, tmp.name)  # noqa: S310 - trusted release URL
        archive = tmp.name

    if archive.endswith(".zip") or url.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(index_dir)
    else:
        with tarfile.open(archive) as tf:
            tf.extractall(index_dir)  # noqa: S202 - trusted release artifact

    print(f"index restored to {index_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
