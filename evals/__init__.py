"""Quality gate. Runnable in CI, not a notebook.

Four frozen datasets, shared metric implementations, and one runner per quality dimension.
All runners default to the configured provider (``fake`` offline) so they work with no
credentials, and write a Markdown report under ``evals/reports/``.
"""
