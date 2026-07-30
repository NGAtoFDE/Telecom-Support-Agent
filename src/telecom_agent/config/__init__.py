"""
Configuration package.

This package provides centralized access to the application's
configuration.

Example
-------
    from telecom_agent.config import settings

    print(settings.app.name)
    print(settings.database.url)
"""

from telecom_agent.config.settings import (
    Settings,
    get_settings,
    settings,
)

__all__ = [
    "Settings",
    "get_settings",
    "settings",
]