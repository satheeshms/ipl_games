import json
from collections import defaultdict

with open('data/ipl_data.json') as f:
    d = json.load(f)

team_season = defaultdict(lambda: defaultdict(int))
for pt in d['player_teams']:
    team_season[pt['season']][pt['team_name']] += 1

print("Season | Teams | Avg squad size")
for season in sorted(team_season):
    teams = team_season[season]
    avg = sum(teams.values()) / len(teams)
    print(f"  {season}: {len(teams)} teams, avg {avg:.0f} players/team")
