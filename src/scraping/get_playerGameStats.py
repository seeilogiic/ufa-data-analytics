import requests
import os
import json
import time

# Set ROOT to the project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

YEARS = ["2021", "2022", "2023", "2024", "2025", "2026"]

url = "https://www.backend.ufastats.com/api/v1/playerGameStats"

src_data_root = os.path.join(ROOT, "src", "data")

# Team stat fields to aggregate per-game (used by compute_standings for team_stats.json)
TEAM_STAT_FIELDS = [
    "goals", "completions", "throwAttempts", "throwaways", "stalls",
    "blocks", "hucksAttempted", "hucksCompleted",
]

for year in YEARS:
    games_path = os.path.join(src_data_root, year, "games.json")
    if not os.path.exists(games_path):
        print(f"[WARN] No games.json for {year}, skipping")
        continue

    with open(games_path) as f:
        games = json.load(f)

    # Accumulators for the two derived output files
    gp_acc = {}          # playerID -> {teamID, gamesPlayed}
    team_game_stats = [] # [{gameID, teams: {teamID: {goals, completions, ...}}}]

    sorted_games = sorted(games.get("data", []), key=lambda g: g.get("startTimestamp", ""))
    total = len(sorted_games)

    for idx, game in enumerate(sorted_games, 1):
        game_id = game.get("gameID")
        if not game_id:
            continue

        response = requests.get(url, params={"gameID": game_id})
        time.sleep(0.1)  # Sleep for 100ms to avoid overwhelming the server
        print(f"[INFO] [{year}] {idx}/{total} gameID={game_id} — status {response.status_code}")

        try:
            data = response.json()
        except Exception as e:
            print(f"[ERROR] Could not parse JSON for gameID {game_id}: {e}")
            continue

        players = data.get("data", [])

        # --- games_played accumulator ---
        # Only count a game if the player had >= 1 O point or >= 1 D point
        for p in players:
            pid = p.get("player", {}).get("playerID")
            tid = p.get("teamID")
            if not pid or not tid:
                continue
            if (p.get("oPointsPlayed") or 0) < 1 and (p.get("dPointsPlayed") or 0) < 1:
                continue
            if pid not in gp_acc:
                gp_acc[pid] = {"teamID": tid, "gamesPlayed": 0}
            gp_acc[pid]["gamesPlayed"] += 1

        # --- team_game_stats accumulator ---
        game_teams = {}
        for p in players:
            tid = p.get("teamID")
            if not tid:
                continue
            if tid not in game_teams:
                game_teams[tid] = {f: 0 for f in TEAM_STAT_FIELDS}
            for field in TEAM_STAT_FIELDS:
                game_teams[tid][field] += p.get(field, 0)

        team_game_stats.append({"gameID": game_id, "teams": game_teams})

    year_dir = os.path.join(src_data_root, year)
    os.makedirs(year_dir, exist_ok=True)

    # Save games_played.json  [{playerID, teamID, gamesPlayed}]
    gp_list = [
        {"playerID": pid, "teamID": v["teamID"], "gamesPlayed": v["gamesPlayed"]}
        for pid, v in gp_acc.items()
    ]
    gp_path = os.path.join(year_dir, "games_played.json")
    with open(gp_path, "w") as f:
        json.dump(gp_list, f, indent=2)
    print(f"[INFO] games_played saved to {gp_path}")

    # Save team_game_stats.json  [{gameID, teams: {teamID: {goals, ...}}}]
    tgs_path = os.path.join(year_dir, "team_game_stats.json")
    with open(tgs_path, "w") as f:
        json.dump(team_game_stats, f, indent=2)
    print(f"[INFO] team_game_stats saved to {tgs_path}")
