import requests
import os
import json

url = "https://www.backend.ufastats.com/api/v1/players"
parameters = {
    "years": "all",
}

response = requests.get(url, params=parameters)

print(f"[INFO] Status code: {response.status_code}")
data = response.json()

# Sort the players by playerID (newest to oldest)
if "data" in data:
    data["data"] = sorted(data["data"], key=lambda x: x["playerID"], reverse=False)


# Group players by year based on their 'teams' array
players_by_year = {}
if "data" in data:
    for player in data["data"]:
        if "teams" in player:
            for team in player["teams"]:
                year = str(team.get("year")) if "year" in team and str(team.get("year")).isdigit() else None
                if year:
                    players_by_year.setdefault(year, []).append(player)

# Save each year's players to its own folder
for year, players in players_by_year.items():
    year_dir = os.path.join("data", year)
    os.makedirs(year_dir, exist_ok=True)
    out_data = {"object": "list", "data": players}
    with open(os.path.join(year_dir, "players.json"), "w") as f:
        json.dump(out_data, f, indent=2)
    print(f"[INFO] Data saved to {os.path.join(year_dir, 'players.json')}")
