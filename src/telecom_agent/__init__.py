"""Telecom Support Agent — network issue triage & escalation.

Installable package (``pip install -e .``). All runtime code lives here so imports
are identical in tests, CI and the container. The ``ui/`` package deliberately sits
outside this tree: it is a separate deployable that talks to the API over HTTP only.
"""

__version__ = "0.1.0"
