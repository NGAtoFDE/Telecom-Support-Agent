"""Loads prompts by ``name@version`` from ``prompts/<name>/v<n>.yaml``.

A prompt is a reviewable YAML asset holding the template, its required variables, an
optional output-schema note and a changelog line. Code never contains prompt text; it
asks the registry for ``("classifier", "v2")`` and renders it with keyword variables.
Missing variables fail loudly rather than producing a silently broken prompt.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from string import Formatter

import yaml

_PROMPTS_DIR = Path(__file__).parent


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    template: str
    variables: tuple[str, ...]
    description: str = ""
    output_schema: str = ""

    def render(self, **kwargs: object) -> str:
        missing = [v for v in self.variables if v not in kwargs]
        if missing:
            raise KeyError(f"prompt {self.name}@{self.version} missing variables: {missing}")
        return self.template.format(**kwargs)


def _referenced_fields(template: str) -> set[str]:
    return {fn for _, fn, _, _ in Formatter().parse(template) if fn}


@lru_cache(maxsize=128)
def get_prompt(name: str, version: str) -> Prompt:
    path = _PROMPTS_DIR / name / f"{version}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"prompt not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    template = data.get("template", "")
    declared = tuple(data.get("variables", []))
    # sanity: every declared variable must actually appear in the template
    fields = _referenced_fields(template)
    undeclared = fields - set(declared)
    if undeclared:
        raise ValueError(f"prompt {name}@{version} uses undeclared variables {sorted(undeclared)}")
    return Prompt(
        name=name,
        version=version,
        template=template,
        variables=declared,
        description=data.get("description", ""),
        output_schema=data.get("output_schema", ""),
    )


def render(name: str, version: str, **kwargs: object) -> str:
    return get_prompt(name, version).render(**kwargs)
