import json
from collections import defaultdict

with open('data/ipl_data.json') as f:
    d = json.load(f)

print('=== POOL SIZES ===')
print('orange_cap:', len(set(a['player_name'] for a in d['awards'] if a['type']=='orange_cap')))
print('purple_cap:', len(set(a['player_name'] for a in d['awards'] if a['type']=='purple_cap')))
print('player_of_tournament:', len(set(a['player_name'] for a in d['awards'] if a['type']=='player_of_tournament')))
print('costliest_player:', len(set(a['player_name'] for a in d['awards'] if a['type']=='costliest_player')))
print('winning_captain:', len(set(a['player_name'] for a in d['awards'] if a['type']=='winning_captain')))
print('ipl_champions:', len(set(w['team_name'] for w in d['ipl_wins'])))
print('batting_records:', len(d['records']['batting_records']))
print('bowling_records:', len(d['records']['bowling_records']))
print('season_records:', len(d['records']['season_records']))
print('fielding_records:', len(d['records']['fielding_records']))
print('team_owners:', len(d['records']['team_owners']))
print('high_strike_rate_batsmen:', len(d['high_strike_rate_batsmen']))
print('highest_batting_avg:', len(d['highest_batting_avg']))
print('catches_by_fielder:', len(d['catches_by_fielder']))
print('dismissals_by_keeper:', len(d['dismissals_by_keeper']))
print('allrounders:', len(d['allrounders']))
print('five_wicket_hauls:', len(d['five_wicket_hauls']))
print('batting_career_stats:', len(d['batting_career_stats']))
print('bowling_career_stats:', len(d['bowling_career_stats']))
print('multi_team_players:', len(d['multi_team_players']))
print('most_ducks:', len(d['most_ducks']))
print('foreign_players:', len(d['foreign_players']))
print('india_state_wise groups:', len(d['india_state_wise']))
print('ranji_team_wise groups:', len(d['ranji_team_wise']))

head_seasons = sorted(set(c['season'] for c in d['coaches'] if c.get('role','head')=='head'))
batting_seasons = sorted(set(c['season'] for c in d['coaches'] if c.get('role')=='batting'))
bowling_seasons = sorted(set(c['season'] for c in d['coaches'] if c.get('role')=='bowling'))
fielding_seasons = sorted(set(c['season'] for c in d['coaches'] if c.get('role')=='fielding'))
print('head coach seasons:', head_seasons)
print('batting coach seasons:', batting_seasons)
print('bowling coach seasons:', bowling_seasons)
print('fielding coach seasons:', fielding_seasons)

# Count coaches per season
print('\n=== HEAD COACHES PER SEASON ===')
for s in head_seasons:
    n = len(set(c['coach'] for c in d['coaches'] if c['season']==s and c.get('role','head')=='head'))
    print(f'  {s}: {n}')
