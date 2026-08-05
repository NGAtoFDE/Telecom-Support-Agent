import os
from dotenv import load_dotenv
import httpx

load_dotenv()

url = os.environ.get("JIRA_URL")
email = os.environ.get("JIRA_USER_EMAIL")
token = os.environ.get("JIRA_API_TOKEN")

print(f"URL: {url}")
payload = {
    "fields": {
        "project": {"key": "SCRUM"},
        "summary": "Test issue",
        "description": "Test description",
        "issuetype": {"name": "Task"}
    }
}

try:
    with httpx.Client(auth=(email, token)) as client:
        resp = client.post(
            f"{url}/rest/api/2/issue",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print("Status code:", resp.status_code)
        print("Response text:", resp.text)
except Exception as e:
    print("Exception:", e)
