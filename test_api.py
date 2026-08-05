"""Send a request to the running API and capture the full response with debug info."""
import requests
import json

API = "http://localhost:8001"
API_KEY = "dev-key-change-me"

# Create a new session
print("=== Creating session ===")
resp = requests.post(
    f"{API}/v1/chat",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={"message": "my internet speed is slow since yesterday"},
    timeout=60,
)
print(f"Status: {resp.status_code}")
data = resp.json()

# Check what resolution we got
print("\n=== KEY RESULTS ===")
print(f"Full JSON: {json.dumps(data, indent=2)}")

if "citations" in data:
        print(f"[{c.get('doc_id')}] score={c.get('score')} - {c.get('title')}")

if data.get("debug"):
    debug = data["debug"]
    print(f"\nProvider: {debug.get('provider')}")
    print(f"Degraded: {debug.get('degraded')}")
    print(f"Groundedness: {debug.get('groundedness')}")
    print(f"Attempt: {debug.get('attempt')}")
