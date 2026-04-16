import requests
import os
import json
import time

# Set ROOT to the project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

url = "https://www.backend.ufastats.com/api/v1/playerStats"

players_path = os.path.join(ROOT, "docs", "data", "players.json")
with open(players_path) as f:
    players = json.load(f)

# Collect all player stats
all_player_stats = []

# Collect all player stats in batches of 100 playerIDs
player_ids = [player['playerID'] for player in players['data']]

batch_size = 100  # Define the batch size
for i in range(0, len(player_ids), batch_size):
    batch = player_ids[i:i+batch_size]
    parameters = { "playerIDs": ','.join(batch) }
    response = requests.get(url, params=parameters)
    time.sleep(1)  # Sleep for 1 second to avoid overwhelming the server
    print(f"[INFO] Fetched player stats for playerIDs: {batch} with status code: {response.status_code}")
    try:
        data = response.json()
        all_player_stats.append({"playerIDs": batch, "data": data})
    except Exception as e:
        print(f"[ERROR] Could not parse JSON for playerIDs {batch}: {e}")

# Group player stats by year using the nested structure
player_stats_by_year = {}
for batch in all_player_stats:
    # batch["data"] is a dict with "object": "list", "data": [ ... ]
    stats_list = batch["data"].get("data", []) if isinstance(batch["data"], dict) else []
    for stat in stats_list:
        year = str(stat.get("year")) if "year" in stat and str(stat.get("year")).isdigit() else None
        if year:
            player_stats_by_year.setdefault(year, []).append(stat)

# Save each year's player stats to its own folder
for year, stats in player_stats_by_year.items():
    year_dir = os.path.join(ROOT, "docs", "data", year)
    os.makedirs(year_dir, exist_ok=True)
    out_path = os.path.join(year_dir, "player_stats.json")
    with open(out_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"[INFO] Data saved to {out_path}")
