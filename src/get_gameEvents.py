import requests
import os
import json
import time

url = "https://www.backend.ufastats.com/api/v1/gameEvents"

with open("data/games.json") as f:
    games = json.load(f)


# Collect all game events
all_game_events = []

for game in games['data']:
    parameters = { "gameID": game['gameID'] }
    response = requests.get(url, params=parameters)
    time.sleep(0.1)  # Sleep for 100ms to avoid overwhelming the server
    print(f"[INFO] Fetched game events for gameID: {game['gameID']} with status code: {response.status_code}")
    try:
        data = response.json()
        all_game_events.append({"gameID": game['gameID'], "data": data})
    except Exception as e:
        print(f"[ERROR] Could not parse JSON for gameID {game['gameID']}: {e}")


# Group game events by year (extract from gameID or from games.json if available)
game_events_by_year = {}
for event in all_game_events:
    game_id = event.get("gameID", "")
    # Try to extract year from gameID (format: YYYY-MM-DD-...)
    year = game_id[0:4] if len(game_id) >= 4 and game_id[0:4].isdigit() else None
    if year:
        game_events_by_year.setdefault(year, []).append(event)

# Save each year's game events to its own folder
for year, events in game_events_by_year.items():
    year_dir = os.path.join("data", year)
    os.makedirs(year_dir, exist_ok=True)
    with open(os.path.join(year_dir, "game_events.json"), "w") as f:
        json.dump(events, f, indent=2)
    print(f"[INFO] Data saved to {os.path.join(year_dir, 'game_events.json')}")
