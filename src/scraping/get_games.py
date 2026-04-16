import requests
import os
import json
import os

url = "https://www.backend.ufastats.com/api/v1/games"
parameters = {
    "date": "2020:",
}

response = requests.get(url, params=parameters)

print(f"[INFO] Status code: {response.status_code}")
data = response.json()


# Group games by year
games_by_year = {}
if "data" in data:
    for game in data["data"]:
        # Extract year from startTimestamp (format: YYYY-MM-DD...)
        year = game.get("startTimestamp", "")[0:4]
        if year.isdigit():
            games_by_year.setdefault(year, []).append(game)

# Save each year's games to its own folder
for year, games in games_by_year.items():
    year_dir = os.path.join("data", year)
    os.makedirs(year_dir, exist_ok=True)
    out_data = {"object": "list", "data": games}
    with open(os.path.join(year_dir, "games.json"), "w") as f:
        json.dump(out_data, f, indent=2)
    print(f"[INFO] Data saved to {os.path.join(year_dir, 'games.json')}")
