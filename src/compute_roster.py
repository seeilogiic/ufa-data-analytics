#!/usr/bin/env python3
"""
Merge per-year player, player_stats, and games_played into a single
roster.json per year.

Inputs:  src/data/{year}/players.json, player_stats.json, games_played.json
Outputs: docs/data/{year}/roster.json

Each entry:
{
  "playerID":     "bjagt",
  "firstName":    "Ben",
  "lastName":     "Jagt",
  "teamID":       "empire",
  "gp":           12,
  "oPointsPlayed": 180,
  "dPointsPlayed": 42,
  "goals":        10,
  "assists":      25,
  "blocks":        8,
  "throwaways":    3,
  "yardsReceived": 800,
  "yardsThrown":   150
}
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DATA_DIR = os.path.join(ROOT, "src", "data")
OUT_DATA_DIR = os.path.join(ROOT, "docs", "data")


def load_json(path):
    with open(path) as f:
        return json.load(f)


def compute_roster(year):
    year_dir = os.path.join(SRC_DATA_DIR, str(year))
    players_path = os.path.join(year_dir, "players.json")
    stats_path   = os.path.join(year_dir, "player_stats.json")
    gp_path      = os.path.join(year_dir, "games_played.json")

    if not os.path.exists(players_path):
        return None

    players_data = load_json(players_path)

    # Build stats lookup: playerID -> stat dict
    stats_map = {}
    if os.path.exists(stats_path):
        for s in load_json(stats_path).get("data", []):
            stats_map[s["playerID"]] = s

    # Build games-played lookup: playerID -> gamesPlayed
    gp_map = {}
    if os.path.exists(gp_path):
        for entry in load_json(gp_path):
            gp_map[entry["playerID"]] = entry["gamesPlayed"]

    roster = []
    for p in players_data.get("data", []):
        pid = p["playerID"]
        s = stats_map.get(pid, {})
        roster.append({
            "playerID":      pid,
            "firstName":     p["firstName"],
            "lastName":      p["lastName"],
            "teamID":        p["teamID"],
            "jerseyNumber":  p.get("jerseyNumber", ""),
            "gp":            gp_map.get(pid, 0),
            "oPointsPlayed": s.get("oPointsPlayed") or 0,
            "dPointsPlayed": s.get("dPointsPlayed") or 0,
            "goals":         s.get("goals") or 0,
            "assists":       s.get("assists") or 0,
            "blocks":        s.get("blocks") or 0,
            "throwaways":    s.get("throwaways") or 0,
            "yardsReceived": s.get("yardsReceived") or 0,
            "yardsThrown":   s.get("yardsThrown") or 0,
        })

    return roster


def main():
    years = sorted(d for d in os.listdir(SRC_DATA_DIR) if d.isdigit())
    for year in years:
        print(f"[{year}] Computing roster…")
        roster = compute_roster(year)
        if roster is None:
            print(f"[{year}] Skipped (no players.json)")
            continue

        out_year_dir = os.path.join(OUT_DATA_DIR, year)
        os.makedirs(out_year_dir, exist_ok=True)
        out_path = os.path.join(out_year_dir, "roster.json")
        with open(out_path, "w") as f:
            json.dump(roster, f, indent=2)
        print(f"[{year}]   Roster ({len(roster)} players) → {out_path}")


if __name__ == "__main__":
    main()
