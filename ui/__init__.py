"""Streamlit support console — a standalone HTTP client for the Telecom Support Agent API.

This package deliberately lives OUTSIDE ``src/telecom_agent`` and must never import from it
(README §8): it is a separate deployable image that talks to the API over HTTP only.
"""
