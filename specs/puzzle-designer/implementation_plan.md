# IPL Connections — Puzzle Designer Implementation Plan

**Spec Version:** 1.0
**Date:** 2026-03-22
**Status:** Draft
**Branch:** puzzle-designer

---

## 1. Design Philosophy

### The Problem with Repetition
A 67-day daily puzzle that rotates the same few category types (team squads, awards, coaches) becomes predictable by week 2. The player stops learning and starts pattern-matching. The game dies.

### The Solution: Variety as a Core Mechanic
Each puzzle should feel like a mini-discovery. The player should think: *"I didn't know CSK and MI shared that many players"*, *"I had no idea 4 of these players are from Karnataka"*, *"Wait, all of these guys played Ranji for Mumbai?"*

The category structure itself is part of the fun — not just the items.

---

## 2. Fan Base & Engagement Research

### 2.1 Team Popularity Tiers

Teams should appear in easier categories proportional to their fan base — casual fans should recognize the items.

| Tier | Teams | Rationale | Frequency in Yellow/Green |
|------|-------|-----------|--------------------------|
| **Mega** | MI, CSK, RCB, KKR | 5+5+0+3 titles, largest social followings, iconic players (Dhoni, Kohli, Rohit, SRK) | 50% of team-based categories |
| **Large** | RR, SRH | RR (inaugural winners, Warne legacy), SRH (Warner era, 1 title) | 25% of team-based categories |
| **Growing** | DC, PBKS, GT, LSG | DC (perpetual underdogs), PBKS (Preity), GT (debut title 2022), LSG (newest) | 25% of team-based categories |

### 2.1.1 Key Rivalries

| Rivalry | Why It Matters | Category Potential |
|---------|---------------|-------------------|
| **CSK vs MI** | "El Clasico" of IPL. 5 titles each. Most played fixture. Rohit vs Dhoni (until 2024). | `played_both:CSK:MI` (17 players) |
| **CSK vs RCB** | Dhoni vs Kohli — the two biggest individual fan bases in Indian cricket. Every match is a cultural event. | `played_both:CSK:RCB` (23 players) |
| **KKR vs MI** | SRK vs Ambani. KKR's 2012/2014 title runs. Recent 2024 dominance. | `played_both:KKR:MI` (26 players) |
| **RCB vs MI** | Kohli vs Rohit — India's ODI/Test captaincy split. RCB's perpetual heartbreak vs MI's ruthless winning. | `played_both:RCB:MI` |

### 2.2 Memorable Seasons (safe to use for category themes)

| Season | Why It's Memorable | Safe for Puzzles? |
|--------|-------------------|-------------------|
| 2008 | Inaugural — RR underdogs win, every OG fan remembers | Yes — nostalgia factor |
| 2011 | CSK back-to-back, Dhoni peak | Yes — iconic |
| 2013 | Spot-fixing scandal, removed teams | Partially — the drama, not the scandal |
| 2016 | Kohli's 973 runs, RCB heartbreak final | Yes — legendary individual season |
| 2019 | MI's 1-run final win vs CSK | Yes — greatest final ever |
| 2020 | UAE bubble season, MI dominant | Yes — unique COVID era |
| 2022 | GT wins title in debut season | Yes — fairy tale |
| 2024 | KKR dominant, 3rd title | Yes — recent memory |
| 2025 | Last completed season | Yes — fresh memory |
| 2026 | Current season | Yes — engagement anchor |

**Rule: Avoid heavy reliance on random middle seasons (2012, 2014, 2017) unless tied to a specific narrative.**

### 2.3 The Golden Era (2008-2013) — Millennial Nostalgia

The IPL's first six seasons featured international legends playing alongside emerging Indian stars. Millennials (born ~1985-2000) were 12-25 during this era — peak nostalgia-formation years. Puzzles themed around this era create emotional engagement that pure stats can't.

#### Indian Legends in IPL (2008-2013)

| Player | IPL Teams | Seasons | Why They Matter |
|--------|-----------|---------|-----------------|
| SR Tendulkar | MI | 2008-2013 | God of Cricket. MI icon. 2010 double century era. |
| R Dravid | RR, RCB | 2008-2013 | The Wall. RR captain 2012-13. Quiet dignity in T20 chaos. |
| SC Ganguly | KKR | 2008-2012 | Dada. KKR's first captain. Bengal's pride. |
| VVS Laxman | DCH, SRH | 2008-2012 | Very Very Special. Hyderabad's own. |
| A Kumble | RCB, MI | 2008-2010 | Jumbo. RCB's first captain. |
| Z Khan | MI, RCB, DCH | 2008-2013 | India's premier left-arm seamer in T20. |
| Harbhajan Singh | MI, CSK | 2008-2019 | Turbanator. MI stalwart. CSK later years. |
| YK Pathan | RR, KKR | 2008-2017 | Inaugural IPL's breakout star. RR hero. |

#### Foreign Legends in IPL (2008-2013)

| Player | IPL Teams | Seasons | Why They Matter |
|--------|-----------|---------|-----------------|
| S Warne | RR | 2008-2011 | Captain of inaugural champions. Spinning legend. |
| AC Gilchrist | DCH | 2008-2013 | Won 2009 title. Explosive keeper-bat. |
| RT Ponting | KKR, MI | 2008-2013 | Ricky Ponting in KKR. Australia's greatest captain. |
| JH Kallis | RCB, KKR | 2008-2014 | Greatest all-rounder ever. Purple Cap 2009 (joint). |
| KP Pietersen | RCB, DC, DD | 2009-2014 | KP switch-hit. Entertainer. |
| M Muralitharan | CSK, RCB | 2008-2014 | Highest wicket-taker in cricket history, in IPL! |
| DL Vettori | RCB | 2008-2012 | RCB captain. NZ's greatest left-arm spinner. |
| A Symonds | DCH, MI | 2008-2011 | Roy. Explosive Aussie all-rounder. |
| SM Pollock | MI | 2008 | South Africa's bowling legend in inaugural IPL. |
| MEK Hussey | CSK | 2008-2013 | Mr. Cricket. CSK's "Sixer Machine" super-sub. |

**Design principle:** Use 2008-2013 squads for Green categories paired with current squads in Yellow. This creates "then vs now" contrast that millennials love. Reserve these for mid-season when casual fans have been hooked and the audience skews more nostalgic.

**New category types for this era:**
- `legends:india` — Indian Test legends who played IPL (Tendulkar, Dravid, Ganguly, Laxman, Kumble, etc.)
- `legends:overseas` — Foreign Test legends in IPL (Warne, Gilchrist, Ponting, Kallis, Pietersen, etc.)
- `team_squad:TEAM:2008-2013` — Squads from specific memorable early seasons

### 2.4 Most Recognizable Players (engagement anchors)

Players who should appear in Yellow/Green categories (casual fans know them):

**All-Time Legends:** MS Dhoni, V Kohli, RG Sharma, AB de Villiers, CH Gayle, SR Watson, SR Tendulkar
**Golden Era Icons:** R Dravid, SC Ganguly, S Warne, AC Gilchrist, RT Ponting, JH Kallis
**Active Stars:** JJ Bumrah, SA Yadav, HH Pandya, RA Jadeja, YBK Jaiswal
**Overseas Icons:** DJ Bravo, SP Narine, DA Warner, F du Plessis, KL Rahul

**Rule: At least 1-2 recognizable names should appear in every puzzle's Yellow or Green category.**

---

## 3. Category Taxonomy & Complexity Ratings

### 3.1 Complexity Scale

| Level | Color | Description | Target Player |
|-------|-------|-------------|---------------|
| **1 — Easy** | Yellow | Current season, big names, popular teams. Solvable by anyone who watches IPL casually. | Casual viewer |
| **2 — Medium** | Green | Historical awards, well-known stats, common foreign countries. Requires a few seasons of following IPL. | Regular watcher |
| **3 — Hard** | Blue | Deep stats, coaching staffs, geographic origins, cross-team transfers. Requires dedicated IPL knowledge. | Serious fan |
| **4 — Expert** | Purple | Ranji connections, obscure records, ducks, multi-team nomads, wordplay. Only cricket nerds get these. | Cricket nerd |

### 3.2 Category Registry

#### GROUP A: Team-Based (who played where)

| Category Spec | Description | Pool Size | Complexity | Max Uses (67 days) |
|---------------|-------------|-----------|------------|---------------------|
| `team_squad:TEAM:2026` | Current season squad | ~25/team | 1 | Backbone — rotate teams |
| `team_squad:TEAM:2025` | Last season squad | ~25/team | 1-2 | 8-10 uses |
| `team_squad:TEAM:2008` | Inaugural season squad | ~15/team (7 teams) | 2 | 4-5 uses |
| `team_all_time:TEAM` | Any player who ever played for team | 130-194/team | 2-3 | 6-8 uses |
| `team_legends:TEAM` | Top run/wicket performers for a team | ~15/team | 2 | 5 uses |
| `winning_squad:SEASON` | Players from the championship-winning team that season | 15-23/season (17 seasons) | 2 | 8-10 uses |

#### GROUP B: Awards & Achievements

| Category Spec | Description | Pool Size | Complexity | Max Uses |
|---------------|-------------|-----------|------------|----------|
| `orange_cap` | Top batter of each season | 18 unique | 2 | 4 |
| `purple_cap` | Top bowler of each season | 18 unique | 2 | 4 |
| `winning_captain` | Captains who lifted the trophy | 18 (many repeats: Dhoni 5×, Rohit 5×) | 2 | 3 |
| `ipl_champions` | Winning team names | 7 unique teams | 1 | 1 (very limited) |
| `costliest_player` | Highest auction buys | 19 unique | 2-3 | 4 |
| `player_of_tournament` | Season MVPs | 18 unique | 3 | 4 |

#### GROUP C: Statistical

| Category Spec | Description | Pool Size | Complexity | Max Uses |
|---------------|-------------|-----------|------------|----------|
| `top_run_scorers` | All-time highest run scorers (3000+ runs filter) | 28 | 2 | 6 |
| `top_wicket_takers` | All-time highest wicket takers (100+ wickets filter) | 29 | 2 | 6 |
| `highest_batting_avg` | Best batting averages (min 20 matches) | 72 | 3 | 8+ |
| `high_strike_rate` | Most aggressive batsmen | 100 | 3 | 8+ |
| `most_fifties` | Players with 20+ IPL fifties | 73 | 3 | 8+ |
| `fifers` | 5-wicket haul achievers | 33 | 3 | 4-5 |
| `most_matches` | Players with most IPL appearances | 100 | 2-3 | 8+ |
| `most_ducks` | Most ducks — fun/embarrassing | 21 | 4 | 3-4 |
| `catches_by_fielder` | Best catchers (non-keeper) | 100 | 3 | 8+ |
| `dismissals_by_keeper` | Best wicket-keepers by dismissals | 19 | 3-4 | 3-4 |
| `allrounders` | IPL all-rounders | 11 | 3-4 | 2 |
| `batting_records` | Individual career record holders | 8 | 4 | 1 |
| `bowling_records` | Individual career record holders | 8 | 4 | 1 |
| `season_records` | Season-specific record holders | 5 | 4 | 1 |
| `fielding_records` | Fielding record holders | 5 | 4 | 1 |

#### GROUP D: Geographic (NEW — uses enriched player data)

| Category Spec | Description | Pool Size | Complexity | Max Uses |
|---------------|-------------|-----------|------------|----------|
| `country:Australia` | Australian IPL players | 69 | 2-3 | 6+ |
| `country:South_Africa` | South African IPL players | 46 | 2-3 | 5+ |
| `country:England` | English IPL players | 30 | 3 | 4 |
| `country:New_Zealand` | NZ IPL players | 29 | 3 | 4 |
| `country:Sri_Lanka` | Sri Lankan IPL players | 31 | 3 | 4 |
| `country:West_Indies` | Caribbean IPL players | 19 | 3 | 3 |
| `country:Afghanistan` | Afghan IPL players | 9 | 4 | 1-2 |
| `state:Maharashtra` | IPL players from Maharashtra | 30 | 3-4 | 4 |
| `state:Delhi` | IPL players from Delhi | 22 | 3-4 | 3 |
| `state:Punjab` | IPL players from Punjab | 22 | 3-4 | 3 |
| `state:Karnataka` | IPL players from Karnataka | 20 | 3-4 | 3 |
| `state:Tamil_Nadu` | IPL players from Tamil Nadu | 19 | 3-4 | 3 |
| `state:UP` | IPL players from Uttar Pradesh | 25 | 3-4 | 4 |
| `ranji:Mumbai` | Played Ranji for Mumbai | 33 | 4 | 4 |
| `ranji:Delhi` | Played Ranji for Delhi | 32 | 4 | 4 |
| `ranji:Karnataka` | Played Ranji for Karnataka | 25 | 4 | 3 |

#### GROUP E: Cross-Team & Relational (NEW)

| Category Spec | Description | Pool Size | Complexity | Max Uses |
|---------------|-------------|-----------|------------|----------|
| `played_both:CSK:MI` | Played for both CSK and MI | 17 | 3-4 | 2-3 |
| `played_both:CSK:RCB` | Played for both CSK and RCB (Dhoni vs Kohli worlds) | 23 | 3-4 | 3 |
| `played_both:RCB:MI` | Played for both RCB and MI (Kohli vs Rohit) | ~20 | 3-4 | 3 |
| `played_both:KKR:MI` | Played for both KKR and MI | 26 | 3-4 | 3 |
| `multi_team:5+` | Played for 5+ teams | 37 | 4 | 4 |
| `multi_team:7+` | Played for 7+ teams (nomads) | ~10 | 4 | 1-2 |
| `longest_serving` | 15+ IPL seasons | ~15 | 3 | 2-3 |
| `legends:india` | Indian Test legends who played IPL (Tendulkar, Dravid, Ganguly, etc.) | ~12 | 2-3 | 2 |
| `legends:overseas` | Foreign legends in IPL (Warne, Gilchrist, Ponting, Kallis, etc.) | ~15 | 2-3 | 2-3 |

#### GROUP F: Team Management

| Category Spec | Description | Pool Size | Complexity | Max Uses |
|---------------|-------------|-----------|------------|----------|
| `coaches:SEASON` | Head coaches of a given season | ~8-10 | 3 | 5-6 (spread across seasons) |
| `coaches:TEAM:SEASON` | All coaching staff for a team in a season (head, batting, bowling, fielding) | 4/team (36 unique across 10 teams) | 3 | 8+ (rotate teams/seasons) |
| `team_owners` | Franchise owners | 10 | 2 | 2 |

---

## 4. Schedule Design Principles

### Principle 1: The "4 Worlds" Rule
Each puzzle's 4 categories must come from 4 DIFFERENT category groups (A-F). A puzzle with 4 team-squad categories is boring. A puzzle with 1 team-squad + 1 award + 1 stat + 1 geography is interesting.

**Bad:** Yellow=team_squad:CSK, Green=team_squad:MI, Blue=team_squad:KKR, Purple=team_squad:RR
**Good:** Yellow=team_squad:CSK:2026, Green=orange_cap, Blue=country:Australia, Purple=ranji:Mumbai

### Principle 2: Match-Day Anchoring
On days when Team X plays Team Y:
- Yellow category should feature Team X or Team Y's current squad
- This creates real-time engagement — fans are already thinking about these teams

### Principle 3: Complexity Gradient
- **Weeks 1-2 (Pre-IPL + early):** More Yellow/Green categories overall. Build the habit loop. Easy enough to share results without frustration.
- **Weeks 3-6 (Mid-season):** Standard difficulty. Blue categories become more challenging.
- **Weeks 7-9 (Business end + playoffs):** Peak difficulty. Only engaged fans remain — reward them with creative Purple categories.

### Principle 4: Signature Puzzles (Every ~7th Puzzle)
Special theme puzzles that break the pattern and create social media moments:

| Edition | Theme | Description |
|---------|-------|-------------|
| Ed 7 | **CSK vs MI: El Clasico** | `played_both:CSK:MI`, rival captains, rival squads (2026 + 2008) |
| Ed 14 | **Dhoni vs Kohli: The Fanbases** | `played_both:CSK:RCB`, CSK squad, RCB squad, winning_captain |
| Ed 21 | **Foreign Invasion** | Country-based categories (Australia, SA, England, West Indies) |
| Ed 28 | **Golden Era (2008-2013)** | `legends:india`, `legends:overseas`, `team_squad:RR:2008`, inaugural award winners — pure millennial nostalgia |
| Ed 35 | **Geography Quiz** | State + Ranji + Country categories — "where are they from?" |
| Ed 42 | **Numbers Game** | Statistical categories (averages, strike rates, ducks, fifties) |
| Ed 49 | **Underdogs & Minnows** | GT/LSG/defunct teams (Kochi, Pune Warriors, Deccan Chargers) |
| Ed 56 | **Record Breakers** | Batting + bowling + fielding + season records — one-time-use categories |
| Ed 60+ | **Playoff Specials** | Tailored to the teams that qualify |

### Principle 5: Category Group Weekly Rotation
To prevent staleness, each week should have a rough pattern that ensures variety across the 7 days:

| Weekday | Yellow (Easy) | Green (Medium) | Blue (Hard) | Purple (Expert) |
|---------|--------------|----------------|-------------|-----------------|
| Day 1 | Team Squad 2026 | Awards | Stats (batting) | Geographic (state) |
| Day 2 | Team Squad 2026 | Top Run Scorers | Country-based | Cross-team |
| Day 3 | Team Squad 2025 | Top Wicket Takers | Coaches | Records |
| Day 4 | Team Squad 2026 | Awards | Stats (bowling) | Geographic (ranji) |
| Day 5 | Team Squad 2026 | Country-based | Fielding stats | Multi-team nomads |
| Day 6 | Team Legends | Awards | Stats (batting avg) | Most Ducks |
| Day 7 | **Signature** | **Signature** | **Signature** | **Signature** |

This is a template, not a rigid grid — the scheduler can adapt based on cooldowns and availability.

### Principle 6: Red Herring Engineering
The best puzzles are the ones where items SEEM to belong to multiple categories. When designing, prefer category combinations where:
- A player in "Orange Cap Winners" also played for the team in the team squad category
- A player in "Country: Australia" could also be in "Played for both MI and CSK"
- A stat-based category player overlaps with a geographic category

This should be a manual review step, not automated.

---

## 5. Cooldown Rules Engine

### 5.1 Hard Rules (enforced by scheduler)

| Rule | Scope | Cooldown |
|------|-------|----------|
| Same `category_group:type` | e.g., `orange_cap` cannot repeat | 4 days |
| Same team in Yellow/Green | e.g., if CSK in Yellow today, no CSK in Yellow/Green for 3 days | 3 days |
| Same player | If "V Kohli" appears today, he cannot appear for 4 days | 4 days |
| Same player in same category | "V Kohli" in `orange_cap` category — never again (lifetime) | Lifetime |
| Same country in geography slot | If `country:Australia` on day N, not again until day N+4 | 4 days |
| Same state in geography slot | If `state:Maharashtra` on day N, not again until day N+4 | 4 days |

### 5.2 Soft Rules (guidelines, can be overridden)

| Rule | Description |
|------|-------------|
| Fan base balance | Mega-tier teams (MI/CSK/RCB/KKR) should appear in Yellow/Green 50% of the time |
| Star player presence | At least 1 widely-known player per puzzle in Yellow/Green |
| Category group diversity | Each puzzle should span at least 3 different category groups (A-F) |
| Weekly stat variety | Don't use the same statistical sub-type (batting vs bowling vs fielding) on consecutive days |
| Signature spacing | Signature puzzles every 6-8 days, not more often |

---

## 6. New Category Generators Needed

The following generators need to be implemented in `category_generators.py`:

### 6.1 Geographic Generators

```
country:COUNTRY          — 4 foreign players from given country
state:STATE              — 4 Indian players from given state
ranji:TEAM               — 4 players who played Ranji for given team
```

**Data source:** `ipl_data.json` → `foreign_players` (country), `india_state_wise` (state), `ranji_team_wise` (ranji)

### 6.2 Cross-Team & Legends Generators

```
played_both:TEAM1:TEAM2  — 4 players who played for both teams
multi_team:N+            — 4 players who played for N+ different teams
longest_serving          — 4 players with most IPL seasons (15+)
legends:india            — 4 Indian Test legends who played IPL (Tendulkar, Dravid, Ganguly, Laxman, Kumble, Zaheer, Harbhajan, Yuvraj, Sehwag, etc.)
legends:overseas         — 4 foreign Test legends in IPL (Warne, Gilchrist, Ponting, Kallis, Pietersen, Muralitharan, Pollock, Vettori, Hussey, Symonds, etc.)
```

**Data source:** `player_teams` (computed at generation time). For `legends`, a curated list of ~12 Indian and ~15 overseas legends is defined as a constant (not auto-derived — these are editorial picks, not statistical).

### 6.3 Team & Management Generators

```
winning_squad:SEASON     — 4 players from the championship-winning team that season (pool: 15-23/season, 17 seasons)
coaches:TEAM:SEASON      — 4 coaching staff for a team in a season (head, batting, bowling, fielding coaches)
```

**Data source:** `ipl_data.json` → `ipl_wins` (winning team + season) cross-referenced with `player_teams` for winning squad. `coaches` data already in ipl_data for coaching staff.

### 6.4 Enhanced Stat Generators

```
top_run_scorers          — 4 from all-time top run scorers (pool: 28, filtered to 3000+ runs)
top_wicket_takers        — 4 from all-time top wicket takers (pool: 29, filtered to 100+ wickets)
most_fifties             — 4 players with most IPL fifties (pool: 73)
most_matches             — 4 players with most IPL appearances (pool: 100)
team_legends:TEAM        — 4 highest run/wicket players for a specific team
```

**Data source:** `manual_top_run_batsmen.json`, `manual_top_bowlers.json`, `manual_fifties.json`, `manual_most_matches.json`, `team_*.json`

---

## 7. Curation Schedule Format

The `curation_schedule.md` is the working document that `schedule_runner.py` reads.

### 7.1 Table Format

```markdown
| Ed | Date    | Day | Match Context       | Yellow                  | Green           | Blue                 | Purple              | Status |
|----|---------|-----|---------------------|-------------------------|-----------------|----------------------|---------------------|--------|
| 1  | 23 Mar  | Mon | Pre-IPL             | `ipl_champions`         | `orange_cap`    | `country:Australia`  | `ranji:Mumbai`      | [ ]    |
| 6  | 28 Mar  | Sat | KKR vs RCB          | `team_squad:KKR:2026`   | `top_run_scorers` | `coaches:2025`     | `played_both:KKR:RCB` | [ ] |
```

### 7.2 Status Values

| Status | Meaning |
|--------|---------|
| `[ ]` | Specs defined, not yet generated |
| `[g]` | Generated (puzzle JSON written), pending review |
| `[r]` | Reviewed and approved |
| `[x]` | Published |
| `[!]` | Needs manual attention |

---

## 8. Implementation Phases

### Phase 1 — Category Generator Implementation
**Goal:** Implement all new generators from §6.

**Tasks:**
- [ ] `country:COUNTRY` generator using `foreign_players` data
- [ ] `state:STATE` generator using `india_state_wise` data
- [ ] `ranji:TEAM` generator using `ranji_team_wise` data
- [ ] `played_both:TEAM1:TEAM2` generator using `player_teams` data
- [ ] `multi_team:N+` generator
- [ ] `longest_serving` generator
- [ ] `legends:india` generator (curated list of Indian Test legends in IPL)
- [ ] `legends:overseas` generator (curated list of foreign Test legends in IPL)
- [ ] `winning_squad:SEASON` generator using ipl_wins + player_teams data
- [ ] `coaches:TEAM:SEASON` generator using coaches data (4 roles per team)
- [ ] `top_run_scorers` generator using manual_top_run_batsmen.json (3000+ runs filter)
- [ ] `top_wicket_takers` generator using manual_top_bowlers.json (100+ wickets filter)
- [ ] `most_fifties` generator
- [ ] `most_matches` generator
- [ ] `team_legends:TEAM` generator
- [ ] Unit tests for all new generators
- [ ] Audit existing generators (`high_strike_rate`, `highest_batting_avg`, `catches_by_fielder`, `dismissals_by_keeper`, `allrounders`) — referenced but not implemented

### Phase 2 — Schedule Generation Algorithm
**Goal:** Build a smarter `gen_schedule_v5.py` that applies all design principles.

**Tasks:**
- [ ] Define the full category inventory with complexity ratings (as code constants)
- [ ] Implement cooldown engine (4-day category, 3-day team, 4-day player, lifetime player-category)
- [ ] Implement fan-base weighting for Yellow/Green team selection
- [ ] Implement "4 Worlds" constraint (categories from different groups)
- [ ] Implement signature puzzle placement (every ~7 days)
- [ ] Implement match-day anchoring (IPL 2026 fixture list → team in Yellow)
- [ ] Generate `curation_schedule.md` with all 67 rows
- [ ] Pool usage summary with exhaustion warnings

### Phase 3 — Puzzle Generation & Review
**Goal:** Generate all 67 puzzles and review them.

**Batches:**
| Batch | Editions | Dates | Target |
|-------|----------|-------|--------|
| Pre-IPL | Ed 1-3 | 25-27 Mar | Generate by 24 Mar |
| Phase 1 | Ed 4-19 | 28 Mar - 12 Apr | Generate by 26 Mar |
| Phase 2a | Ed 22-35 | 13-26 Apr | Generate by 10 Apr |
| Phase 2b | Ed 36-50 | 27 Apr - 11 May | Generate by 24 Apr |
| Phase 2c | Ed 51-60 | 12-21 May | Generate by 8 May |
| Playoffs | Ed 61-67 | 22-31 May | Generate when teams confirmed |

**For each batch:**
1. Run `schedule_runner.py --from DATE --to DATE --dry-run`
2. Fix any pool exhaustion errors
3. Run without `--dry-run`
4. Manual review using checklist (§9)
5. Update `curation_schedule.md` status to `[r]`
6. Commit puzzle JSONs

### Phase 4 — Playoff Adaptation
**Goal:** Handle playoff puzzles where teams aren't known in advance.

- Ed 61-66: Leave specs as `team_squad:QUALIFIER_1:2026` etc.
- Once qualifiers are determined (~19 May), replace placeholders with real team codes
- Generate with `--force` flag
- Ed 67 (Final): generate only after Qualifier 2

---

## 9. Review Checklist

### Automated Checks
- [ ] No item appears twice in the same puzzle
- [ ] No item collision with any previously published puzzle
- [ ] All 4 categories have exactly 4 items
- [ ] All hashes round-trip correctly
- [ ] Category specs match the schedule

### Content Quality
- [ ] All 16 items are real, verifiable IPL facts/names
- [ ] Yellow: solvable by someone who just follows IPL scores
- [ ] Green: solvable by someone who has watched IPL for 2+ years
- [ ] Blue: requires specific knowledge but answer is unambiguous
- [ ] Purple: creative/tricky but not unfair — there IS a findable connection
- [ ] At least 1-2 widely-known players in Yellow or Green categories

### Red Herring Check
- [ ] At least 2 items across the 16 plausibly belong to 2 different categories
- [ ] No item OBVIOUSLY belongs to only one category (too easy)
- [ ] No category title that directly spoils another category

### Diversity Check
- [ ] Not all 4 categories are player-name lists (mix in teams, coaches, records when possible)
- [ ] Mix of Indian and overseas players
- [ ] Not all 4 categories from the same era/season
- [ ] Adjacent puzzles (±1 day) don't share the same team theme in Yellow

---

## 10. Pool Capacity Planning (65 Puzzles)

Pre-IPL reduced from 5 to 3 puzzles (Ed 1-3: 25-27 Mar), bringing total from 67 to 65 editions.

Each puzzle uses 16 items (4 categories x 4 items). Total items needed: 65 x 16 = **1,040 items**.

With the player-level lifetime cooldown (same player never in same category type), we need to track usage carefully.

**Comfortable categories (10+ uses available):**
- `most_matches` (100), `high_strike_rate` (100), `catches_by_fielder` (100)
- `most_fifties` (73), `highest_batting_avg` (72), `team_squad:TEAM:SEASON` (unlimited rotation)
- `country:Australia` (69), `country:South_Africa` (46)
- `winning_squad:SEASON` (15-23/season, 17 seasons — massive combined pool)

**Moderate categories (4-8 uses):**
- `top_run_scorers` (28, 3000+ runs filter) — 6 uses, `top_wicket_takers` (29, 100+ wickets filter) — 6 uses
- Awards (orange_cap, purple_cap, etc.) — 18 each, ~4 uses
- `fifers` (33), `multi_team:5+` (37), `most_ducks` (21)
- Geographic: `state:Maharashtra` (30), `state:UP` (25), `ranji:Mumbai` (33)
- `country:England` (30), `country:NZ` (29), `country:SL` (31)
- `coaches:TEAM:SEASON` (4 coaches/team, 36 unique/season) — 8+ uses rotating teams/seasons

**Limited categories (1-2 uses — use strategically):**
- `batting_records` (8), `bowling_records` (8) — 1 use each
- `season_records` (5), `fielding_records` (5) — 1 use each
- `allrounders` (11) — 2 uses
- `ipl_champions` (7 unique teams) — 1 use
- `country:Afghanistan` (9) — 1-2 uses
- `multi_team:7+` (~10) — 1 use
- `dismissals_by_keeper` (19) — 3-4 uses

---

## 11. Open Questions

| # | Question | Default |
|---|----------|---------|
| 1 | Should match-day fixture list be hardcoded or fetched? | Hardcode for 2026 season |
| 2 | Should signature puzzles be pre-designed manually or auto-generated? | Manual design for maximum creativity |
| 3 | Need IPL 2026 squad data — is it loaded? | Verify `team_squad:TEAM:2026` data exists |
| 4 | Should we create "difficulty rating" metadata in each puzzle JSON? | Nice-to-have for v2 |
| 5 | Cross-team categories (`played_both`) — which rivalry pairs are most engaging? | CSK-MI (El Clasico), CSK-RCB (Dhoni vs Kohli), KKR-MI (SRK vs Ambani), RCB-MI (Kohli vs Rohit) |
| 6 | Should we weight toward Indian players in easy categories? | Yes — core audience is Indian |
| 7 | How many legend players do we have in the data for 2008-2013 era? | Audit `player_teams` for Tendulkar, Dravid, Ganguly, Laxman, Kumble, Sehwag, Warne, Gilchrist, Ponting, Kallis presence |
| 8 | Pre-IPL puzzle count? | **Resolved: 3 puzzles** (Ed 1-3, 25-27 Mar) |
