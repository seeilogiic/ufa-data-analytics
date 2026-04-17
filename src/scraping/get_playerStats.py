import requests
import os
import json
import time

# Set ROOT to the project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

YEARS = ["2021", "2022", "2023", "2024", "2025", "2026"]

url = "https://www.backend.ufastats.com/api/v1/playerStats"

# Only the fields actually rendered in the roster table
KEEP_STAT_FIELDS = {
    "goals", "assists", "blocks", "throwaways", "stalls",
    "oPointsPlayed", "dPointsPlayed",
    "yardsReceived", "yardsThrown",
    "completions", "throwAttempts",
    "hucksAttempted", "hucksCompleted",
}

src_data_root = os.path.join(ROOT, "src", "data")

# Collect unique player IDs from src/data/{year}/players.json (2021+ only)
seen_ids = set()
player_ids = []
for year in sorted(YEARS):
    players_path = os.path.join(src_data_root, year, "players.json")
    if not os.path.exists(players_path):
        continue
    with open(players_path) as f:
        players_data = json.load(f)
    for player in players_data.get("data", []):
        pid = player.get("playerID")
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            player_ids.append(pid)

if not player_ids:
    print(f"[ERROR] No player IDs found under {src_data_root}")
    raise SystemExit(1)

print(f"[INFO] Fetching stats for {len(player_ids)} players")

# Fetch stats in batches of 100, group by year
stats_by_year = {}
batch_size = 100
for i in range(0, len(player_ids), batch_size):
    batch = player_ids[i : i + batch_size]
    parameters = {"playerIDs": ",".join(str(p) for p in batch), "years": ",".join(YEARS)}
    response = requests.get(url, params=parameters)
    time.sleep(1)  # Sleep for 1 second to avoid overwhelming the server
    print(f"[INFO] Batch {i // batch_size + 1} — status {response.status_code}")
    try:
        data = response.json()
        for stat in data.get("data", []):
            year = str(stat.get("year"))
            if year not in YEARS:
                continue
            # Keep only player identity + needed stat fields
            trimmed = {
                "playerID": stat["player"]["playerID"],
                "year":     stat["year"],
            }
            for field in KEEP_STAT_FIELDS:
                trimmed[field] = stat.get(field)
            stats_by_year.setdefault(year, []).append(trimmed)
    except Exception as e:
        print(f"[ERROR] Could not parse JSON for batch starting at {i}: {e}")

# Save each year's stats to src/data/{year}/player_stats.json (intermediate, not served)
for year, stats in stats_by_year.items():
    year_dir = os.path.join(src_data_root, year)
    os.makedirs(year_dir, exist_ok=True)
    out_path = os.path.join(year_dir, "player_stats.json")
    with open(out_path, "w") as f:
        json.dump({"object": "list", "data": stats}, f, indent=2)
    print(f"[INFO] Player stats saved to {out_path}")

