import requests
import os
import json
import time

# Set ROOT to the project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

url = "https://www.backend.ufastats.com/api/v1/playerStats"

data_root = os.path.join(ROOT, "docs", "data")

# Collect all unique player IDs from every year's players.json
seen_ids = set()
player_ids = []
if os.path.exists(data_root):
    for entry in sorted(os.listdir(data_root)):
        players_path = os.path.join(data_root, entry, "players.json")
        if os.path.exists(players_path):
            with open(players_path) as f:
                players_data = json.load(f)
            for player in players_data.get("data", []):
                pid = player.get("playerID")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    player_ids.append(pid)

if not player_ids:
    print(f"[ERROR] No player IDs found under {data_root}")

# Fetch stats in batches, group by the 'year' field returned by the API
stats_by_year = {}
batch_size = 100
for i in range(0, len(player_ids), batch_size):
    batch = player_ids[i:i + batch_size]
    parameters = {"playerIDs": ",".join(str(p) for p in batch)}
    response = requests.get(url, params=parameters)
    time.sleep(1)  # Sleep for 1 second to avoid overwhelming the server
    print(f"[INFO] Fetched player stats batch {i // batch_size + 1} with status code: {response.status_code}")
    try:
        data = response.json()
        for stat in data.get("data", []):
            year = str(stat.get("year")) if "year" in stat and str(stat.get("year")).isdigit() else None
            if year:
                stats_by_year.setdefault(year, []).append(stat)
    except Exception as e:
        print(f"[ERROR] Could not parse JSON for batch starting at {i}: {e}")

# Save each year's stats to the correct year folder
for year, stats in stats_by_year.items():
    year_dir = os.path.join(data_root, year)
    os.makedirs(year_dir, exist_ok=True)
    out_path = os.path.join(year_dir, "player_stats.json")
    with open(out_path, "w") as f:
        json.dump({"object": "list", "data": stats}, f, indent=2)
    print(f"[INFO] Data saved to {out_path}")

