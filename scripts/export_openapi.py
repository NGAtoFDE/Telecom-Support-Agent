#!/usr/bin/env python
"""Regenerate docs/openapi.json from the live FastAPI app.

Committing the generated spec means a breaking API change shows up as a diff in review
(README §7).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from telecom_agent.api.main import create_app


def main() -> int:
    app = create_app()
    spec = app.openapi()
    out = Path("docs/openapi.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(spec.get('paths', {}))} paths)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
