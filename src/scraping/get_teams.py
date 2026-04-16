import requests
import os
import json

url = "https://www.backend.ufastats.com/api/v1/teams"
parameters = {
    "years": "all",
}

response = requests.get(url, params=parameters)

print(f"[INFO] Status code: {response.status_code}")
data = response.json()

# Sort the teams by teamID (newest to oldest)
if "data" in data:
    data["data"] = sorted(data["data"], key=lambda x: x["teamID"], reverse=False)


# Group teams by year based on the 'year' field
teams_by_year = {}
if "data" in data:
    for team in data["data"]:
        year = str(team.get("year")) if "year" in team and str(team.get("year")).isdigit() else None
        if year:
            teams_by_year.setdefault(year, []).append(team)

# Save each year's teams to its own folder
for year, teams in teams_by_year.items():
    year_dir = os.path.join("data", year)
    os.makedirs(year_dir, exist_ok=True)
    out_data = {"object": "list", "data": teams}
    with open(os.path.join(year_dir, "teams.json"), "w") as f:
        json.dump(out_data, f, indent=2)
    print(f"[INFO] Data saved to {os.path.join(year_dir, 'teams.json')}")
