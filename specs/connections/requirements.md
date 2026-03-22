# IPL Cluster 4 — Requirements

**Game:** IPL Cluster 4
**Spec Version:** 1.0
**Date:** 2026-03-14
**Status:** Draft

---

## 1. Overview

IPL Cluster 4 is a daily word/item puzzle game inspired by the NYTimes Connections (Sports Edition). Players are presented with 16 IPL-related items arranged in a 4×4 grid and must sort them into 4 hidden groups of 4, each sharing a common IPL theme or category. The game is scoped for the IPL season and targets cricket fans.

---

## 2. Goals

- Deliver a daily engaging puzzle tied to IPL trivia and knowledge.
- Mirror the NYTimes Connections UX: intuitive, mobile-first, shareable.
- Require no backend interaction to verify answers (client-side hash check).
- Build a habit loop: one puzzle per day, results shareable without spoilers.

---

## 3. Game Mechanics

### 3.1 Grid

- 16 items displayed in a 4×4 grid.
- Items are words, names, phrases, or abbreviations drawn from IPL data (players, teams, venues, statistics, seasons, records, slogans, etc.).
- Grid is shuffled on load to avoid revealing grouping patterns.
- Player can re-shuffle at any time.

### 3.2 Categories

- Exactly 4 categories, each containing exactly 4 items.
- Each category has:
  - A **color** indicating difficulty (see §3.3).
  - A **category title** revealed only after the group is correctly identified.
- Puzzle designers must include deliberate **red-herring items** — items that appear to belong to multiple categories to create challenge.

### 3.3 Difficulty Colors

| Color  | Level    | Description |
|--------|----------|-------------|
| Yellow | Easiest  | Obvious IPL groupings (e.g., "IPL Teams" / "Chennai Super Kings Players") |
| Green  | Moderate | Requires moderate IPL knowledge (e.g., "Purple Cap Winners") |
| Blue   | Hard     | Nuanced facts or less-known trivia (e.g., "Captains who won IPL in their debut season") |
| Purple | Hardest  | Wordplay, puns, or obscure connections (e.g., "IPL player nicknames", "Words hidden in player names") |

### 3.4 Selection & Submission

- Player taps/clicks up to 4 items to select a group.
- "Submit" is enabled only when exactly 4 items are selected.
- On submission:
  - **Correct:** Group is removed from grid and displayed above it with its color and category title.
  - **One Away:** Show hint "One Away!" if 3 of 4 selected items are from the same correct group.
  - **Incorrect:** Deduct one life; selected items deselect.
- Player has **4 lives** (mistakes allowed). Losing all 4 ends the game.
- On win or loss, all unrevealed categories are revealed with their titles.

### 3.5 Deselect / Undo

- Clicking a selected item deselects it.
- A "Deselect All" button clears the current selection.

---

## 4. IPL-Specific Content Categories (Examples)

These are illustrative category themes — puzzles can combine any of the following:

| Theme Area | Example Category | Example Items |
|---|---|---|
| Teams | "IPL Teams (2024 Season)" | CSK, MI, RCB, KKR |
| Players by team | "RCB Players" | Virat Kohli, Faf du Plessis, Glenn Maxwell, Mohammed Siraj |
| Record holders | "Most IPL Centuries" | Virat Kohli, David Warner, Chris Gayle, Rohit Sharma |
| Venues | "Chennai Venues" | Chepauk, MA Chidambaram Stadium, same item variations |
| Captains | "IPL Winning Captains" | MS Dhoni, Rohit Sharma, Gautam Gambhir, David Warner |
| Award winners | "Orange Cap Winners" | David Warner, Virat Kohli, Ruturaj Gaikwad, Shikhar Dhawan |
| Award winners | "Purple Cap Winners" | Dwayne Bravo, Bhuvneshwar Kumar, Harshal Patel, Yuzvendra Chahal |
| Nicknames | "Player Nicknames" | Thala, Hitman, King, Universe Boss |
| Jersey numbers | "Retired IPL Jersey Numbers" | 7, 10, 18, 45 |
| Slogans | "Team Slogans / War Cries" | Yellove, Paltan, Ee Sala Cup Namde, Korbo Lorbo Jeetbo |
| Wordplay | "Players whose names contain a cricket term" | SIXth Tendulkar → SIX, BOWLing → BOWL, etc. |
| Season records | "IPL 2023 Records" | — |
| Coaches | "IPL Coaches" | — |
| Commentators | "Iconic IPL Commentators" | — |

Puzzle creators are expected to expand this list each season using the data pipeline.

---

## 5. Daily Puzzle System

### 5.1 Puzzle Generation

- One puzzle is published per day, aligned with IPL season calendar.
- Off-season: puzzles can still run as "IPL Classic" using historical data.
- Puzzle date maps to a deterministic puzzle ID (e.g., `YYYY-MM-DD`).
- Puzzles are pre-generated and stored as static JSON files (no runtime generation).

### 5.2 Puzzle JSON Schema

```json
{
  "id": "2026-03-15",
  "date": "2026-03-15",
  "edition": 1,
  "categories": [
    {
      "title": "CSK Players",
      "color": "yellow",
      "items": ["MS Dhoni", "Ruturaj Gaikwad", "Deepak Chahar", "Ravindra Jadeja"]
    },
    {
      "title": "Purple Cap Winners",
      "color": "green",
      "items": ["Dwayne Bravo", "Bhuvneshwar Kumar", "Harshal Patel", "Yuzvendra Chahal"]
    },
    {
      "title": "IPL Winning Captains (first time)",
      "color": "blue",
      "items": ["Shane Warne", "Adam Gilchrist", "Gautam Gambhir", "Rohit Sharma"]
    },
    {
      "title": "Player Nicknames",
      "color": "purple",
      "items": ["Thala", "Hitman", "King", "Universe Boss"]
    }
  ],
  "answerHash": "<sha256 of canonical answer string>"
}
```

### 5.3 Answer Verification (Client-Side)

- The correct groupings are encoded in the puzzle JSON and hashed (SHA-256).
- On submit, the client reconstructs the answer key from selected items, hashes it, and compares against `answerHash`.
- No API call is made to verify answers. The puzzle JSON itself does **not** expose category membership directly — items are listed flat in the grid payload; category membership is encoded only in the hash.
- Hash input format: sorted category items joined deterministically (e.g., alphabetically sorted items per category, categories sorted by color order).

> **Security note:** Since this is a fun game and not high-stakes, the hash scheme is sufficient to prevent casual cheating. The full solution is technically derivable client-side; this is acceptable.

---

## 6. User Session & Progress

- Session state stored in **browser localStorage** (no login required).
- State stored per puzzle ID:
  - Completed categories (colors revealed)
  - Remaining lives
  - Submitted guesses (for replay protection)
  - Win/loss status
- On revisit to the same day's puzzle, state is restored exactly.
- State resets automatically when the next day's puzzle loads.
- Optional: cookie-based fallback for localStorage-restricted environments.

---

## 7. Sharing

- On game end (win or loss), a "Share Results" button appears.
- Share output format (no spoilers, emoji grid):

```
IPL Cluster 4 #42 — 14 Mar 2026
🟨🟨🟨🟨
🟩🟩🟩🟩
🟦🟦🟦🟦
🟪🟪🟪🟪
```

- Each row represents a guess attempt; squares show which color category each item belonged to (reveals guess order, not item names).
- Copies to clipboard on desktop; triggers native share sheet on mobile.
- Share text includes: game name, puzzle number, date, emoji grid.

---

## 8. UI / UX Requirements

### 8.1 Layout

- Mobile-first responsive design.
- Grid: 4 columns × 4 rows of item tiles.
- Tiles: rounded corners, clear text, tap target ≥ 48×48 px.
- Above the grid: revealed category banners (colored, with title).
- Below the grid: lives indicator, Shuffle, Deselect All, Submit buttons.
- Header: game title, date, edition number, help/rules icon.

### 8.2 Visual Design

- Color palette uses IPL-inspired tones (optional theming per team).
- Category difficulty colors: Yellow `#F9DF6D`, Green `#A0C35A`, Blue `#B0C4EF`, Purple `#BA81C5` (matching NYT style closely).
- Incorrect guess: tile shake animation.
- Correct group: tiles fly up and form a banner row.
- "One Away" hint: brief toast notification.

### 8.3 Accessibility

- Keyboard navigable (Tab + Enter to select/submit).
- ARIA labels on all interactive elements.
- Color is not the sole indicator of category — category titles shown on reveal.
- Contrast ratio ≥ 4.5:1 for all text on tile backgrounds.

### 8.4 Rules / Help Modal

- Accessible via "?" icon.
- Explains: objective, color difficulty, lives, one-away hint, sharing.
- Shows an animated example of a correct group reveal.

---

## 9. Data Pipeline Requirements

### 9.1 Data Sources

| Source | Data Obtained |
|--------|--------------|
| Cricbuzz / ESPNCricinfo scraping | Players, teams, stats, match results |
| Kaggle IPL datasets | Historical season data, awards, records |
| CricAPI / Cricsheet | Live/recent season player and match data |
| Manual curation | Nicknames, slogans, wordplay categories |

### 9.2 Pipeline Output

- Structured data stored in a normalized format (JSON / SQLite).
- Data refreshed at start of each IPL season + after major milestones.
- Puzzle curator tool (CLI or admin UI) lets an editor select items and build a puzzle for a given date.

### 9.3 Puzzle Curation

- Puzzle curator selects 4 categories × 4 items from the data store.
- Tool validates: no duplicate items, exactly 4 groups of 4, all items exist in the data store.
- Tool generates `answerHash` and outputs the final puzzle JSON.
- Puzzles are reviewed before publishing to ensure fairness and no unintended double-meanings.

---

## 10. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Performance | Page load < 2s on 4G mobile |
| Offline | Game playable offline after initial load (PWA / service worker) |
| Static hosting | Frontend deployable on GitHub Pages / Vercel / S3 with no server |
| Puzzle freshness | New puzzle available by 12:00 AM IST daily |
| Browser support | Chrome, Safari, Firefox — last 2 major versions |
| Analytics | Optional: privacy-friendly event tracking (puzzle started, completed, shared) |

---

## 11. Out of Scope (v1)

- User accounts / login
- Leaderboards or multiplayer
- Real-time score updates
- Admin CMS (puzzle curation will be CLI-based in v1)
- Notifications / push alerts
- Ads or monetization

---

## 12. Future Considerations

- Archive of past puzzles with replay capability.
- Difficulty selection (Rookie / Pro / Legend mode).
- Team-themed daily puzzles (e.g., "CSK Week").
- Hint system (costs a life to reveal one item's category).
- Integration with live IPL match events for special edition puzzles.
- Localization in Hindi and regional languages.
