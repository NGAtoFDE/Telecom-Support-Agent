"""Jira Client for creating issues in Jira."""

from __future__ import annotations

import httpx
import logging

from telecom_agent.config.settings import Settings

log = logging.getLogger(__name__)

class JiraClient:
    def __init__(self, settings: Settings) -> None:
        self.url = settings.jira_url.rstrip("/")
        self.email = settings.jira_user_email
        self.token = settings.jira_api_token
        self.auth = (self.email, self.token) if self.email and self.token else None

    def create_issue(self, summary: str, description: str, issue_type: str = "Task", project_key: str = "SCRUM") -> str | None:
        """Create a Jira issue and return its key, or None on failure."""
        if not self.url or not self.auth:
            log.warning("Jira not configured, skipping issue creation.")
            return None

        # Atlassian REST API requires issue data in a specific format
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary[:255], # Summary max length is usually 255
                "description": description,
                "issuetype": {"name": issue_type}
            }
        }
        
        try:
            with httpx.Client(auth=self.auth) as client:
                resp = client.post(
                    f"{self.url}/rest/api/2/issue",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("key")
        except Exception as e:
            log.error(f"Failed to create Jira issue: {e}")
            return None
