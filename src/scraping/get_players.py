import requests
import os
import json
import time

# Set ROOT to the project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

url = "https://www.backend.ufastats.com/api/v1/players"
parameters = {
    "years": "all",
}

response = requests.get(url, params=parameters)
time.sleep(0.1)  # Sleep for 100ms to avoid overwhelming the server

print(f"[INFO] Status code: {response.status_code}")
data = response.json()

# Sort the players by playerID (newest to oldest)
if "data" in data:
    data["data"] = sorted(data["data"], key=lambda x: x["playerID"], reverse=False)

# Flatten each player into per-year records: {playerID, firstName, lastName, teamID, active, jerseyNumber, year}
players_by_year = {}
if "data" in data:
    for player in data["data"]:
        for team in player.get("teams", []):
            year = str(team.get("year")) if "year" in team and str(team.get("year")).isdigit() else None
            if year:
                record = {
                    "playerID": player.get("playerID"),
                    "firstName": player.get("firstName"),
                    "lastName": player.get("lastName"),
                    "teamID": team.get("teamID"),
                    "active": team.get("active"),
                    "jerseyNumber": team.get("jerseyNumber"),
                    "year": int(year),
                }
                players_by_year.setdefault(year, []).append(record)

# Save each year's players to its own folder
for year, players in players_by_year.items():
    year_dir = os.path.join(ROOT, "docs", "data", year)
    os.makedirs(year_dir, exist_ok=True)
    out_data = {"object": "list", "data": players}
    out_path = os.path.join(year_dir, "players.json")
    with open(out_path, "w") as f:
        json.dump(out_data, f, indent=2)
    print(f"[INFO] Data saved to {out_path}")
