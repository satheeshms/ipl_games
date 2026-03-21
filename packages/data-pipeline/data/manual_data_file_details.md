# Manual Data Files Documentation

This document provides a comprehensive inventory of all manually curated JSON files in the IPL data pipeline. These files contain statistically verified and curated cricket statistics for the Indian Premier League.

## Overview

The manual JSON files are verified datasets that support the IPL games platform. They contain curated cricket statistics spanning from IPL 2008 to 2025, organized by statistical categories (batting, bowling, fielding, awards, and records).

### Data Standards

**Player Naming Convention**: Uses scorecard initials format (e.g., "V Kohli", "MS Dhoni", "CH Gayle")

**Team Code Format**: Standard IPL team abbreviations
- Active Teams: CSK, MI, KKR, RCB, SRH, DC, RR, GT, LSG, PBKS
- Historical Teams: PWI (Pune Warriors), RPS (Rising Pune Supergiant), GL (Gujarat Lions), DCH (Deccan Chargers), Kochi (Kochi Tuskers Kerala)

**Data Coverage**: IPL Seasons 2008-2025

---

## Quick Summary Table

| # | File Name | Category | Purpose | Data Focus | kaggle_loader.py |
|---|-----------|----------|---------|------------|:----------------:|
| 1 | `manual_awards.json` | Awards & Recognition | Orange Cap, Purple Cap, awards winners | Season awards, auction records | ✅ Step 7 |
| 2 | `manual_coaches.json` | Team Management | Head coach assignments per team | Coaching history 2008-2025 | — |
| 3 | `manual_records.json` | Records & Statistics | Comprehensive IPL records database | Batting, bowling, fielding records | — |
| 4 | `manual_top_run_batsmen.json` | Batting Statistics | Top 100+ batsmen ranked by runs | Career batting stats, centuries | ✅ Step 9 (3000+ runs) |
| 5 | `manual_highest_batting_avg.json` | Batting Statistics | Batsmen ranked by batting average | Efficiency metrics, strike rate | — |
| 6 | `manual_batting_strike_rate.json` | Batting Statistics | Aggressive batsmen by strike rate | Sixes, fours, explosive batting | — |
| 7 | `manual_top_bowlers.json` | Bowling Statistics | Top 100+ bowlers ranked by wickets | Career bowling stats, economy | ✅ Step 10 (100+ wickets) |
| 8 | `manual_4_plus_wickets.json` | Bowling Statistics | 4+ wicket haul performances | Multi-wicket achievements | — |
| — | `manual_most_ducks.json` | Batting Statistics | Players with most ducks | Dismissals for zero, batting vulnerability | ✅ Step 12 (10+ ducks) |
| 9 | `manual_5_plus_wickets.json` | Bowling Statistics | 5+ wicket haul performances | Elite bowling performances | ✅ Step 8 |
| 10 | `manual_most_dismissals_fielder.json` | Fielding & Dismissals | Non-keeper fielding records | Catches, runouts, fielding excellence | — |
| 11 | `manual_most_dismissals_wk.json` | Fielding & Dismissals | Wicket-keeper dismissal records | Catches, stumpings, keeper stats | — |
| 12 | `manual_players_multi_team.json` | Player History | Players across multiple franchises | Player movement, team changes | ✅ Step 11 (5+ teams) |
| 13 | `manual_most_matches.json` | Player History | Most IPL appearances by player | Career longevity, loyalty records | — |
| 14 | `team_[CODE].json` | Team Data | Per-team statistics and rosters | Team squads, performance data | — |
| 15 | `players_master.json` | Master Data | Complete player registry | All players, basic identification | — |
| 16 | `players_master_enriched.json` | Master Data | Extended player dataset | Enhanced player metadata | — |

**Total Files**: 16 primary file categories (plus 15 team-specific files)
**Total Records**: 2000+ player records across all statistics
**Data Span**: IPL Seasons 2008-2025
**Update Frequency**: Seasonal updates

---

## Files Documentation

### Awards & Recognition

#### `manual_awards.json`
**Purpose**: IPL awards across all seasons including Orange Cap, Purple Cap, and auction records

**Structure**:
- Orange Cap winners: Highest run scorer each season (2008-2025)
- Purple Cap winners: Leading wicket taker each season (2008-2025)
- Costliest auction buys: Top purchases from IPL auctions
- Winning captains: Champions and runners-up captains by season
- Player of Tournament: Best performers across seasons

**Usage**: For displaying season awards, achievement records, and historical comparisons

---

### Team Management

#### `manual_coaches.json`
**Purpose**: Head coach assignments for each IPL team across all seasons

**Structure**:
- Organized by team code
- Chronological coaching assignments (2008-2025)
- Both active and historical team coaching histories
- Covers all 10 current teams plus 5 historical franchises

**Usage**: For team history, coaching records, and season-specific team information

---

### Records & Statistics

#### `manual_records.json`
**Purpose**: Comprehensive IPL records database

**Content Categories**:
- **Batting Records**: Highest run scorer, most sixes, most fours, centuries, fifties
- **Bowling Records**: Highest wicket taker, best figures, dot balls bowled, 5-wicket hauls
- **Season Records**: Best team performance, highest/lowest scores
- **Fielding Records**: Best fielding performances, most dismissals (non-keepers)
- **Team Ownership**: Franchise owners and management history

**Usage**: For record displays, achievement comparisons, and historical statistics

---

### Batting Statistics

#### `manual_top_run_batsmen.json`
**Purpose**: Ranked list of top 100+ batsmen in IPL history

**Fields Per Player**:
- Rank, Player name, Teams played for, Career span
- Matches, Innings, Runs, Highest score
- Batting average, Strike rate
- Centuries, Fifties, Ducks
- Fours and Sixes count

**Usage**: For batting leaderboards, player comparisons, and career statistics

---

#### `manual_highest_batting_avg.json`
**Purpose**: Batsmen ranked by batting average (minimum innings requirement)

**Fields**:
- Rank, Player name, Teams
- Innings played, Runs, Batting average
- Strike rate, Centuries, Fifties
- Career span

**Usage**: For identifying most efficient batsmen, performance comparisons

---

#### `manual_batting_strike_rate.json`
**Purpose**: Aggressive batsmen ranked by strike rate

**Fields**:
- Rank, Player name, Teams, Career span
- Matches, Innings, Runs, Strike rate
- Sixes and Fours count
- Batting average

**Usage**: For aggressive batting records, explosive player identification

---

### Bowling Statistics

#### `manual_top_bowlers.json`
**Purpose**: Ranked list of 100+ bowlers in IPL history

**Fields Per Bowler**:
- Rank, Player name, Teams, Career span
- Matches, Innings, Balls bowled, Overs
- Maidens, Runs conceded, Wickets
- Best innings figures, Bowling average
- Economy rate, Strike rate
- 4-wicket and 5-wicket haul counts

**Usage**: For bowling leaderboards, player comparisons, career statistics

---

#### `manual_4_plus_wickets.json`
**Purpose**: Bowling performances with 4+ wicket hauls

**Fields**:
- Rank, Player name, Teams, Career span
- Matches, Innings, Balls, Overs
- Maidens, Runs, Wickets
- Best bowling innings, Bowling average
- Economy, Strike rate
- Count of 4-wicket and 5-wicket hauls

**Usage**: For identifying impactful bowling performances, multi-wicket haul records

---

#### `manual_5_plus_wickets.json`
**Purpose**: Bowling performances with 5+ wicket hauls (rare achievements)

**Fields**: Similar to 4+ wickets file, focused on elite bowling performances

**Usage**: For highlighting rare 5-wicket performances, peak bowling displays

---

### Fielding & Dismissals

#### `manual_most_dismissals_fielder.json`
**Purpose**: Non-keeper fielding records ranked by total dismissals (catches + runouts)

**Fields**:
- Rank, Player name, Teams
- Career span (years active)
- Matches, Innings
- Total dismissals, Catches, Runouts
- Maximum dismissals in single innings

**Usage**: For fielding excellence records, defensive performance comparisons

---

#### `manual_most_dismissals_wk.json`
**Purpose**: Wicket-keeper dismissal records (catches + stumpings)

**Fields**:
- Rank, Player name, Teams
- Career span, Matches, Innings
- Total dismissed, Catches, Stumpings
- Dismissals per innings average
- Maximum dismissals in single innings

**Usage**: For keeper performance records, wicket-keeping excellence leaderboards

---

### Player History

#### `manual_players_multi_team.json`
**Purpose**: Players who have played for multiple IPL teams

**Fields**:
- Player name
- Teams string (comma-separated)
- Team list (array format)
- Total team count

**Usage**: For player career tracking, franchise history, player movement records

---

#### `manual_most_matches.json`
**Purpose**: Players with most IPL appearances

**Fields**:
- Rank, Player name, Teams
- Career span, Matches played
- Innings, Runs, Highest score, Average
- Strike rate, Centuries, Fifties, Ducks
- Fours, Sixes, Status (Active/Retired)

**Usage**: For IPL loyalty records, career longevity comparisons

---

### Team Data Files

#### Team-Specific JSON Files
**Pattern**: `team_[CODE].json` (e.g., team_CSK.json, team_MI.json)

**Purpose**: Per-team statistics and player rosters

**Included Teams**:
- Current teams: CSK, DC, GT, KKR, LSG, MI, PBKS, RCB, RR, SRH
- Historical teams: DCH, GL, KTK, PWI, RPS

**Usage**: For team-specific analytics, squad information, team records

---

### Master Player Data

#### `players_master.json`
**Purpose**: Complete player registry with basic identification

**Content**:
- All players across IPL history
- Player names (standardized format)
- Associated teams
- Career information

**Usage**: For player database queries, team roster lookups

---

#### `players_master_enriched.json`
**Purpose**: Extended player dataset with additional information

**Content**: Enhanced version of players_master with additional metadata fields

**Usage**: For comprehensive player profiles, data enrichment operations

---

## Data Quality Notes

- All player names follow consistent scorecard format for accurate matching
- Team codes are standardized across all files
- Data spans complete IPL history (2008-2025 seasons)
- Statistics are verified and curated for accuracy
- Some players appear in multiple files under different team associations
- Historical team codes are preserved for accurate season-specific records

## Usage in Data Pipeline

These manual files are integrated into the data pipeline for:

1. **Data Validation**: Cross-referencing with scraped data from ESPNcricinfo
2. **Gap Filling**: Supplementing missing statistics from automated sources
3. **Historical Records**: Maintaining complete records of retired players
4. **Awards & Records**: Storing verified championship data and awards
5. **Game Generation**: Providing curated datasets for puzzle generation

## Related Files

- `ipl.db`: SQLite database containing normalized IPL data
- `ipl_data.json`: Compiled JSON export from database
- Python loaders: `kaggle_loader.py`, `squad_loader.py`, `espncricinfo.py`
- Data normalization: `normalizer.py`, `schema.py`

---

**Last Updated**: 2025 IPL Season
**Data Pipeline Version**: Curated IPL Games Dataset v1.0
