#!/usr/bin/env python3
"""
Compute playoff bracket data for all available years.

Outputs docs/data/{year}/bracket.json

Structure:
{
  "hasData": true,
  "divisions": ["Atlantic", "Central", "North", "West"],
  "quarters":  { "Atlantic": <game>, ... },   // one game per div, or null
  "divFinals": { "Atlantic": <game>, ... },
  "semis":     [ <game>, <game> ],
  "championship": <game> or null
}

Each <game> is:
{
  "homeTeamID":   "phoenix",
  "homeTeamName": "Philadelphia Phoenix",
  "homeTeamSeed": 1,
  "homeScore":    15,
  "awayTeamID":   "royal",
  "awayTeamName": "San Jose Spiders",
  "awayTeamSeed": 2,
  "awayScore":    12,
  "winner":       "phoenix"   // null if not yet played
}
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "docs", "data")
WEEK_RE = re.compile(r"^week-\d+$")


def load_json(path):
    with open(path) as f:
        return json.load(f)


def _included_and_postseason(games_data):
    """Separate regular-season games (12-game cap) from postseason overflow."""
    regular_finals = sorted(
        [
            g for g in games_data["data"]
            if g.get("status") == "Final" and WEEK_RE.match(g.get("week") or "")
        ],
        key=lambda g: g.get("startTimestamp") or "",
    )
    team_counts = {}
    postseason = []
    for game in regular_finals:
        a, h = game["awayTeamID"], game["homeTeamID"]
        ac, hc = team_counts.get(a, 0), team_counts.get(h, 0)
        if ac < 12 and hc < 12:
            team_counts[a] = ac + 1
            team_counts[h] = hc + 1
        else:
            postseason.append(game)
    return postseason


def _classify_rounds(playoff_games):
    """Mirror the JS classifyPlayoffRounds logic exactly."""
    if not playoff_games:
        return {"quarters": [], "divFinals": [], "semis": [], "championship": []}

    weeks = {g.get("week") for g in playoff_games}

    # 2024/2025 style – all week-N labels
    week_nums = sorted(
        int(m.group(1)) for w in weeks
        if w and (m := re.match(r"^week-(\d+)$", w))
    )
    if len(week_nums) >= 2:
        by_week = {}
        for g in playoff_games:
            m = re.match(r"^week-(\d+)$", g.get("week") or "")
            if m:
                by_week.setdefault(int(m.group(1)), []).append(g)
        w1, w2 = week_nums[0], week_nums[1]
        w3 = week_nums[2] if len(week_nums) > 2 else None
        last_round = by_week.get(w3, []) if w3 else []
        return {
            "quarters": by_week.get(w1, []),
            "divFinals": by_week.get(w2, []),
            "semis": last_round[:-1],
            "championship": last_round[-1:],
        }

    # 2023 style – named labels
    if weeks & {"playoffs", "divisional-champ", "semi-finals"}:
        all_semis = [g for g in playoff_games if g.get("week") == "semi-finals"]
        return {
            "quarters": [g for g in playoff_games if g.get("week") == "playoffs"],
            "divFinals": [g for g in playoff_games if g.get("week") == "divisional-champ"],
            "semis": all_semis[:-1],
            "championship": all_semis[-1:],
        }

    # 2021/2022 style – championship-weekend
    cw = [g for g in playoff_games if g.get("week") == "championship-weekend"]
    pl = [g for g in playoff_games if g.get("week") == "playoffs"]
    if cw:
        mid = len(pl) // 2
        return {
            "quarters": pl[:mid],
            "divFinals": pl[mid:],
            "semis": cw[:-1],
            "championship": cw[-1:],
        }

    return {"quarters": [], "divFinals": [], "semis": [], "championship": []}


def _make_game_entry(game, team_names, seed_map):
    h_id = game["homeTeamID"]
    a_id = game["awayTeamID"]
    h_score = game.get("homeScore")
    a_score = game.get("awayScore")
    winner = None
    if h_score is not None and a_score is not None:
        if h_score > a_score:
            winner = h_id
        elif a_score > h_score:
            winner = a_id
    return {
        "homeTeamID":   h_id,
        "homeTeamName": team_names.get(h_id, h_id),
        "homeTeamSeed": seed_map.get(h_id),
        "homeScore":    h_score,
        "awayTeamID":   a_id,
        "awayTeamName": team_names.get(a_id, a_id),
        "awayTeamSeed": seed_map.get(a_id),
        "awayScore":    a_score,
        "winner":       winner,
    }


def compute_bracket(year):
    year_dir = os.path.join(DATA_DIR, str(year))
    teams_path = os.path.join(year_dir, "teams.json")
    games_path = os.path.join(year_dir, "games.json")
    standings_path = os.path.join(year_dir, "standings.json")

    if not os.path.exists(teams_path) or not os.path.exists(games_path):
        return None

    teams_data = load_json(teams_path)
    games_data = load_json(games_path)
    team_names = {t["teamID"]: t["name"] for t in teams_data["data"]}

    # Build division membership + seeding from standings (or fall back to teams.json)
    div_teams_map = {}  # divName -> [teamID ordered by seed]
    seed_map = {}       # teamID -> seed number (1-based)

    if os.path.exists(standings_path):
        standings = load_json(standings_path)
        for div_name, entries in standings.items():
            div_teams_map[div_name] = [e["teamID"] for e in entries]
            for entry in entries:
                seed_map[entry["teamID"]] = entry["rank"]
    else:
        for t in teams_data["data"]:
            if t["division"]["divisionID"] != "allstars":
                div_teams_map.setdefault(t["division"]["name"], []).append(t["teamID"])

    team_to_div = {tid: div for div, tids in div_teams_map.items() for tid in tids}

    # Collect playoff games
    postseason_overflow = _included_and_postseason(games_data)
    playoff_labels = {"playoffs", "divisional-champ", "semi-finals", "championship-weekend"}
    labelled = [g for g in games_data["data"] if g.get("status") == "Final" and g.get("week") in playoff_labels]
    all_postseason = labelled if labelled else postseason_overflow

    if not all_postseason:
        return {"hasData": False, "divisions": sorted(div_teams_map.keys())}

    rounds = _classify_rounds(all_postseason)

    divisions = sorted(div_teams_map.keys())

    def game_for_div(games_list, div):
        div_team_ids = set(div_teams_map.get(div, []))
        for g in games_list:
            if g["homeTeamID"] in div_team_ids and g["awayTeamID"] in div_team_ids:
                return _make_game_entry(g, team_names, seed_map)
        return None

    quarters = {div: game_for_div(rounds["quarters"], div) for div in divisions}
    div_finals = {div: game_for_div(rounds["divFinals"], div) for div in divisions}
    semis = [_make_game_entry(g, team_names, seed_map) for g in rounds["semis"]]
    championship = _make_game_entry(rounds["championship"][0], team_names, seed_map) if rounds["championship"] else None

    return {
        "hasData": True,
        "divisions": divisions,
        "quarters": quarters,
        "divFinals": div_finals,
        "semis": semis,
        "championship": championship,
    }


def main():
    years = sorted(d for d in os.listdir(DATA_DIR) if d.isdigit())
    for year in years:
        year_dir = os.path.join(DATA_DIR, year)
        if not os.path.exists(os.path.join(year_dir, "games.json")):
            print(f"[{year}] Skipped (no games.json)")
            continue

        print(f"[{year}] Computing bracket…")
        result = compute_bracket(year)
        if result is None:
            print(f"[{year}] Skipped (missing data)")
            continue

        out_path = os.path.join(year_dir, "bracket.json")
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"[{year}]   Bracket → {out_path}")


if __name__ == "__main__":
    main()
