import requests
import os
import json

url = "https://www.backend.ufastats.com/api/v1/teams"
parameters = {
    "years": "all",
}

response = requests.get(url, params=parameters)

print(f"[INFO] Status code: {response.status_code}")
data = response.json()

# Ensure the data directory exists
os.makedirs("data", exist_ok=True)

# Save the response to a JSON file
with open("data/teams.json", "w") as f:
    json.dump(data, f, indent=2)

print("[INFO] Data saved to data/teams.json")
