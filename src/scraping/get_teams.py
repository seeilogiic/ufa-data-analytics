import requests
import os
import json
import time

# Set ROOT to the project root directory
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

YEARS = ["2021", "2022", "2023", "2024", "2025", "2026"]

url = "https://www.backend.ufastats.com/api/v1/teams"
parameters = {
    "years": ",".join(YEARS),
}

response = requests.get(url, params=parameters)
time.sleep(0.1)  # Sleep for 100ms to avoid overwhelming the server

print(f"[INFO] Status code: {response.status_code}")
data = response.json()

# Fields kept in src/data (intermediate): all fields needed by compute scripts
KEEP_FIELDS = {"teamID", "year", "division", "city", "name", "fullName", "abbrev",
               "wins", "losses", "ties", "standing"}

# Group teams by year, trimming to only needed fields
teams_by_year = {}
for team in sorted(data.get("data", []), key=lambda x: x["teamID"]):
    year = str(team.get("year"))
    if year not in YEARS:
        continue
    trimmed = {k: v for k, v in team.items() if k in KEEP_FIELDS}
    teams_by_year.setdefault(year, []).append(trimmed)

# Save trimmed data to src/data/{year}/teams.json (intermediate, not served)
for year, teams in teams_by_year.items():
    year_dir = os.path.join(ROOT, "src", "data", year)
    os.makedirs(year_dir, exist_ok=True)
    out_path = os.path.join(year_dir, "teams.json")
    with open(out_path, "w") as f:
        json.dump({"object": "list", "data": teams}, f, indent=2)
    print(f"[INFO] Intermediate teams saved to {out_path}")

    # Also write a minimal teams.json to docs/data/{year}/ for HTML year-detection
    # Only includes fields the HTML actually needs: teamID, name, division
    minimal = [
        {"teamID": t["teamID"], "name": t["name"], "division": t["division"]}
        for t in teams
    ]
    docs_dir = os.path.join(ROOT, "docs", "data", year)
    os.makedirs(docs_dir, exist_ok=True)
    docs_path = os.path.join(docs_dir, "teams.json")
    with open(docs_path, "w") as f:
        json.dump({"object": "list", "data": minimal}, f, indent=2)
    print(f"[INFO] Minimal teams saved to {docs_path}")
