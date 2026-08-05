import os
from dotenv import load_dotenv
import httpx

load_dotenv()

APP_ID = os.environ.get("DISCORD_APP_ID")
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

if not APP_ID or not BOT_TOKEN:
    print("Error: DISCORD_APP_ID and DISCORD_BOT_TOKEN must be in .env")
    exit(1)

url = f"https://discord.com/api/v10/applications/{APP_ID}/commands"
headers = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json"
}

command_data = {
    "name": "support",
    "description": "Get help from the Telecom Support Agent",
    "options": [
        {
            "type": 3, # STRING
            "name": "issue",
            "description": "Describe your issue",
            "required": True
        }
    ]
}

response = httpx.post(url, json=command_data, headers=headers)

if response.status_code in [200, 201]:
    print("Successfully registered /support command!")
else:
    print(f"Failed to register command. Status {response.status_code}: {response.text}")
