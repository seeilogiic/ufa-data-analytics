import requests
import os
import json
import time

# Set ROOT to the project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

YEARS = ["2021", "2022", "2023", "2024", "2025", "2026"]

url = "https://www.backend.ufastats.com/api/v1/games"
parameters = {
    "date": "2021:",  # All games from 2021 onward
}

response = requests.get(url, params=parameters)
time.sleep(0.1)  # Sleep for 100ms to avoid overwhelming the server

print(f"[INFO] Status code: {response.status_code}")
data = response.json()

# Fields actually needed by compute_standings and compute_bracket
KEEP_FIELDS = {"gameID", "homeTeamID", "awayTeamID", "homeScore", "awayScore",
               "status", "startTimestamp", "week"}

# Group games by year, trimming to only needed fields
games_by_year = {}
for game in data.get("data", []):
    year = game.get("startTimestamp", "")[0:4]
    if year not in YEARS:
        continue
    trimmed = {k: v for k, v in game.items() if k in KEEP_FIELDS}
    games_by_year.setdefault(year, []).append(trimmed)

# Save each year's games to src/data/{year}/games.json (intermediate, not served)
for year, games in games_by_year.items():
    year_dir = os.path.join(ROOT, "src", "data", year)
    os.makedirs(year_dir, exist_ok=True)
    games_sorted = sorted(games, key=lambda g: g.get("startTimestamp", ""))
    out_path = os.path.join(year_dir, "games.json")
    with open(out_path, "w") as f:
        json.dump({"object": "list", "data": games_sorted}, f, indent=2)
    print(f"[INFO] Games saved to {out_path}")
