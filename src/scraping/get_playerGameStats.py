import requests
import os
import json
import time

# Set ROOT to the project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

url = "https://www.backend.ufastats.com/api/v1/playerGameStats"

games_path = os.path.join(ROOT, "docs", "data", "games.json")
with open(games_path) as f:
    games = json.load(f)

# Collect all player game stats
all_player_game_stats = []

for game in games['data']:
    parameters = { "gameID": game['gameID'] }
    response = requests.get(url, params=parameters)
    time.sleep(0.1)  # Sleep for 100ms to avoid overwhelming the server
    print(f"[INFO] Fetched player stats for gameID: {game['gameID']} with status code: {response.status_code}")
    try:
        data = response.json()
        all_player_game_stats.append({"gameID": game['gameID'], "data": data})
    except Exception as e:
        print(f"[ERROR] Could not parse JSON for gameID {game['gameID']}: {e}")

# Group player game stats by year (extract from gameID)
player_game_stats_by_year = {}
for stat in all_player_game_stats:
    game_id = stat.get("gameID", "")
    year = game_id[0:4] if len(game_id) >= 4 and game_id[0:4].isdigit() else None
    if year:
        player_game_stats_by_year.setdefault(year, []).append(stat)

# Save each year's player game stats to its own folder
for year, stats in player_game_stats_by_year.items():
    year_dir = os.path.join(ROOT, "docs", "data", year)
    os.makedirs(year_dir, exist_ok=True)
    out_path = os.path.join(year_dir, "player_game_stats.json")
    with open(out_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"[INFO] Data saved to {out_path}")
