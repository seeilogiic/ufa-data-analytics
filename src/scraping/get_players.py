import requests
import os
import json
import time

# Set ROOT to the project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

YEARS = ["2021", "2022", "2023", "2024", "2025", "2026"]

url = "https://www.backend.ufastats.com/api/v1/players"
parameters = {
    "years": ",".join(YEARS),
}

response = requests.get(url, params=parameters)
time.sleep(0.1)  # Sleep for 100ms to avoid overwhelming the server

print(f"[INFO] Status code: {response.status_code}")
data = response.json()

# Flatten each player into per-year records keeping only needed fields
players_by_year = {}
for player in sorted(data.get("data", []), key=lambda x: x["playerID"]):
    for team in player.get("teams", []):
        year = str(team.get("year"))
        if year not in YEARS:
            continue
        record = {
            "playerID":    player["playerID"],
            "firstName":   player["firstName"],
            "lastName":    player["lastName"],
            "teamID":      team["teamID"],
            "active":      team["active"],
            "jerseyNumber": team.get("jerseyNumber"),
            "year":        int(year),
        }
        players_by_year.setdefault(year, []).append(record)

# Save each year's players to src/data/{year}/players.json (intermediate, not served)
for year, players in players_by_year.items():
    year_dir = os.path.join(ROOT, "src", "data", year)
    os.makedirs(year_dir, exist_ok=True)
    out_path = os.path.join(year_dir, "players.json")
    with open(out_path, "w") as f:
        json.dump({"object": "list", "data": players}, f, indent=2)
    print(f"[INFO] Players saved to {out_path}")
