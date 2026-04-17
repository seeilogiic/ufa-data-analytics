#!/usr/bin/env python3
"""
Compute regular-season standings and team stats for all available years.

Inputs:  src/data/{year}/games.json, teams.json, team_game_stats.json
Outputs: docs/data/{year}/standings.json, team_stats.json
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DATA_DIR = os.path.join(ROOT, "src", "data")
OUT_DATA_DIR = os.path.join(ROOT, "docs", "data")
WEEK_RE = re.compile(r"^week-\d+$")


def load_json(path):
    with open(path) as f:
        return json.load(f)


def _included_games(games_data):
    """Return the first 12 regular-season (week-N) games per team, in chronological order."""
    regular_finals = sorted(
        [
            g for g in games_data["data"]
            if g.get("status") == "Final" and WEEK_RE.match(g.get("week") or "")
        ],
        key=lambda g: g.get("startTimestamp") or "",
    )
    team_counts = {}
    included = []
    for game in regular_finals:
        a, h = game["awayTeamID"], game["homeTeamID"]
        ac, hc = team_counts.get(a, 0), team_counts.get(h, 0)
        if ac < 12 and hc < 12:
            included.append(game)
            team_counts[a] = ac + 1
            team_counts[h] = hc + 1
    return included


def _head_to_head(team_a, team_b, games):
    a_wins = b_wins = 0
    for g in games:
        a_home = g["homeTeamID"] == team_a and g["awayTeamID"] == team_b
        a_away = g["awayTeamID"] == team_a and g["homeTeamID"] == team_b
        if not a_home and not a_away:
            continue
        a_score = g["homeScore"] if g["homeTeamID"] == team_a else g["awayScore"]
        b_score = g["homeScore"] if g["homeTeamID"] == team_b else g["awayScore"]
        if a_score > b_score:
            a_wins += 1
        elif b_score > a_score:
            b_wins += 1
    return a_wins, b_wins


def _mini_diff(team_id, tie_ids, games):
    diff = 0
    for g in games:
        if g["homeTeamID"] not in tie_ids or g["awayTeamID"] not in tie_ids:
            continue
        if g["homeTeamID"] == team_id:
            diff += g["homeScore"] - g["awayScore"]
        elif g["awayTeamID"] == team_id:
            diff += g["awayScore"] - g["homeScore"]
    return diff


def _sort_division(div_teams, included_games):
    """Sort a division's teams with full tie-breaking logic."""
    div_teams.sort(key=lambda t: (-t["wins"], -t["pct"], t["name"]))

    # Group adjacent teams with identical wins + pct
    groups, cur = [], [div_teams[0]]
    for i in range(1, len(div_teams)):
        prev, curr = div_teams[i - 1], div_teams[i]
        if prev["wins"] == curr["wins"] and abs(prev["pct"] - curr["pct"]) < 1e-6:
            cur.append(curr)
        else:
            groups.append(cur)
            cur = [curr]
    groups.append(cur)

    resolved = []
    for group in groups:
        if len(group) == 1:
            resolved.extend(group)
            continue

        if len(group) == 2:
            A, B = group
            aw, bw = _head_to_head(A["teamID"], B["teamID"], included_games)
            if aw != bw:
                resolved.extend([A, B] if aw > bw else [B, A])
                continue
            tie_ids = {A["teamID"], B["teamID"]}
            am = _mini_diff(A["teamID"], tie_ids, included_games)
            bm = _mini_diff(B["teamID"], tie_ids, included_games)
            if am != bm:
                resolved.extend([A, B] if am > bm else [B, A])
                continue
            if A["plusMinus"] != B["plusMinus"]:
                resolved.extend([A, B] if A["plusMinus"] > B["plusMinus"] else [B, A])
                continue
            resolved.extend(sorted([A, B], key=lambda t: t["name"]))
            continue

        # 3+ team tie: mini-league point differential
        tie_ids = {t["teamID"] for t in group}
        group.sort(key=lambda t: (
            -_mini_diff(t["teamID"], tie_ids, included_games),
            -t["plusMinus"],
            t["name"],
        ))
        resolved.extend(group)

    return resolved


def compute_standings(year):
    year_dir = os.path.join(SRC_DATA_DIR, str(year))
    teams_path = os.path.join(year_dir, "teams.json")
    games_path = os.path.join(year_dir, "games.json")
    if not os.path.exists(teams_path) or not os.path.exists(games_path):
        return None, None

    teams_data = load_json(teams_path)
    games_data = load_json(games_path)
    teams = [t for t in teams_data["data"] if t["division"]["divisionID"] != "allstars"]
    included_games = _included_games(games_data)

    # Build per-team records from included games (not from teams.json totals)
    records = {t["teamID"]: {"wins": 0, "losses": 0, "ties": 0, "plusMinus": 0, "games": 0}
               for t in teams}
    for game in included_games:
        h_id, a_id = game["homeTeamID"], game["awayTeamID"]
        h_s, a_s = game["homeScore"], game["awayScore"]
        home, away = records.get(h_id), records.get(a_id)
        if not home or not away:
            continue
        home["plusMinus"] += h_s - a_s
        away["plusMinus"] += a_s - h_s
        home["games"] += 1
        away["games"] += 1
        if h_s > a_s:
            home["wins"] += 1
            away["losses"] += 1
        elif a_s > h_s:
            away["wins"] += 1
            home["losses"] += 1
        else:
            home["ties"] += 1
            away["ties"] += 1

    # Build division map
    division_map = {}
    for team in teams:
        div = team["division"]["name"]
        rec = records.get(team["teamID"], {"wins": 0, "losses": 0, "ties": 0, "plusMinus": 0, "games": 0})
        g = rec["games"]
        pct = (rec["wins"] + 0.5 * rec["ties"]) / g if g > 0 else 0.0
        # Keep internal game counts for pct and tiebreaks, but do not emit `games` in output
        division_map.setdefault(div, []).append({
            "teamID": team["teamID"],
            "name": team["name"],
            "wins": rec["wins"],
            "losses": rec["losses"],
            "ties": rec["ties"],
            "plusMinus": rec["plusMinus"],
            "pct": pct,
        })

    # Sort each division with tie-breaking, then compute games back
    standings_out = {}
    for div_name in sorted(division_map.keys()):
        sorted_teams = _sort_division(division_map[div_name], included_games)
        leader = sorted_teams[0]
        result = []
        for rank, team in enumerate(sorted_teams, 1):
            gb = ((leader["wins"] - team["wins"]) + (team["losses"] - leader["losses"])) / 2
            # Do not include `games` in the exported standings JSON
            result.append({
                "rank": rank,
                "teamID": team["teamID"],
                "name": team["name"],
                "wins": team["wins"],
                "losses": team["losses"],
                "ties": team["ties"],
                "plusMinus": team["plusMinus"],
                "pct": round(team["pct"], 4),
                "gamesBack": gb,
            })
        standings_out[div_name] = result

    return standings_out, included_games


def compute_team_stats(year, included_games):
    year_dir = os.path.join(SRC_DATA_DIR, str(year))
    teams_path = os.path.join(year_dir, "teams.json")
    tgs_path = os.path.join(year_dir, "team_game_stats.json")
    if not os.path.exists(tgs_path):
        return None

    teams_data = load_json(teams_path)
    tgs_raw = load_json(tgs_path)
    teams = [t for t in teams_data["data"] if t["division"]["divisionID"] != "allstars"]

    # Build a lookup: gameID -> {teamID: {goals, completions, ...}}
    game_stats_map = {entry["gameID"]: entry["teams"] for entry in tgs_raw}

    # Build records from included_games for wins/losses columns
    records = {t["teamID"]: {"wins": 0, "losses": 0, "games": 0} for t in teams}
    for game in included_games:
        h_id, a_id = game["homeTeamID"], game["awayTeamID"]
        h_s, a_s = game["homeScore"], game["awayScore"]
        home, away = records.get(h_id), records.get(a_id)
        if not home or not away:
            continue
        home["games"] += 1
        away["games"] += 1
        if h_s > a_s:
            home["wins"] += 1
            away["losses"] += 1
        elif a_s > h_s:
            away["wins"] += 1
            home["losses"] += 1

    acc = {
        t["teamID"]: {
            "teamID": t["teamID"],
            "name": t["name"],
            "wins": records[t["teamID"]]["wins"],
            "losses": records[t["teamID"]]["losses"],
            "games": records[t["teamID"]]["games"],
            "scores": 0,
            "scoresAgainst": 0,
            "completions": 0,
            "throwAttempts": 0,
            "throwaways": 0,
            "blocks": 0,
            "hucksAttempted": 0,
            "hucksCompleted": 0,
        }
        for t in teams
    }

    for game in included_games:
        game_teams = game_stats_map.get(game["gameID"])
        if not game_teams:
            continue

        for tid, opp_tid in [(game["homeTeamID"], game["awayTeamID"]), (game["awayTeamID"], game["homeTeamID"])]:
            ts = acc.get(tid)
            gt = game_teams.get(tid, {})
            ogt = game_teams.get(opp_tid, {})
            if not ts:
                continue
            ts["scores"]         += gt.get("goals", 0)
            ts["scoresAgainst"]  += ogt.get("goals", 0)
            ts["completions"]    += gt.get("completions", 0)
            ts["throwAttempts"]  += gt.get("throwAttempts", 0)
            ts["throwaways"]     += gt.get("throwaways", 0) + gt.get("stalls", 0)
            ts["blocks"]         += gt.get("blocks", 0)
            ts["hucksAttempted"] += gt.get("hucksAttempted", 0)
            ts["hucksCompleted"] += gt.get("hucksCompleted", 0)

    result = []
    for ts in acc.values():
        ta = ts["throwAttempts"]
        h = ts["hucksAttempted"]
        ts["completionPct"] = round(ts["completions"] / ta * 100, 1) if ta > 0 else None
        ts["huckPct"] = round(ts["hucksCompleted"] / h * 100, 1) if h > 0 else None
        result.append(ts)

    return sorted(result, key=lambda t: (-t["wins"], t["name"]))


def main():
    years = sorted(d for d in os.listdir(SRC_DATA_DIR) if d.isdigit())
    for year in years:
        src_year_dir = os.path.join(SRC_DATA_DIR, year)
        out_year_dir = os.path.join(OUT_DATA_DIR, year)
        if not os.path.exists(os.path.join(src_year_dir, "games.json")):
            print(f"[{year}] Skipped (no games.json)")
            continue

        print(f"[{year}] Computing standings…")
        standings, included_games = compute_standings(year)
        if standings is None:
            print(f"[{year}] Skipped (missing data)")
            continue

        os.makedirs(out_year_dir, exist_ok=True)
        out_path = os.path.join(out_year_dir, "standings.json")
        with open(out_path, "w") as f:
            json.dump(standings, f, indent=2)
        print(f"[{year}]   Standings → {out_path}")

        team_stats = compute_team_stats(year, included_games)
        if team_stats:
            ts_path = os.path.join(out_year_dir, "team_stats.json")
            with open(ts_path, "w") as f:
                json.dump(team_stats, f, indent=2)
            print(f"[{year}]   Team stats → {ts_path}")


if __name__ == "__main__":
    main()
