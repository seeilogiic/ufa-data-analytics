import requests
import os
import json
import time

# Set ROOT to the project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

url = "https://www.backend.ufastats.com/api/v1/gameEvents"

data_root = os.path.join(ROOT, "docs", "data")

# Find all per-year games.json files under docs/data/*/games.json
games_files = []
if os.path.exists(data_root):
    for entry in os.listdir(data_root):
        entry_path = os.path.join(data_root, entry)
        if os.path.isdir(entry_path):
            candidate = os.path.join(entry_path, "games.json")
            if os.path.exists(candidate):
                games_files.append(candidate)

# Fallback: check for a top-level docs/data/games.json
root_games = os.path.join(data_root, "games.json")
if os.path.exists(root_games):
    games_files.append(root_games)

if not games_files:
    print(f"[ERROR] No games.json files found under {data_root}")

for games_path in games_files:
    with open(games_path) as f:
        games = json.load(f)

    # Collect all game events for this year's games, sorted by startTimestamp
    all_game_events = []
    for game in sorted(games.get('data', []), key=lambda g: g.get('startTimestamp', '')):
        parameters = { "gameID": game.get('gameID') }
        if not parameters["gameID"]:
            continue
        response = requests.get(url, params=parameters)
        time.sleep(0.1)  # Sleep for 100ms to avoid overwhelming the server
        print(f"[INFO] Fetched game events for gameID: {parameters['gameID']} with status code: {response.status_code}")
        try:
            data = response.json()
            all_game_events.append({"gameID": parameters['gameID'], "data": data})
        except Exception as e:
            print(f"[ERROR] Could not parse JSON for gameID {parameters['gameID']}: {e}")

    # Determine year folder for this games.json
    year_dir = os.path.dirname(games_path)
    os.makedirs(year_dir, exist_ok=True)
    out_path = os.path.join(year_dir, "game_events.json")
    with open(out_path, "w") as f:
        json.dump(all_game_events, f, indent=2)
    print(f"[INFO] Data saved to {out_path}")
