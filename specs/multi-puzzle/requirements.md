# Multi-Puzzle Interface — Requirements

**Spec Version:** 1.0
**Date:** 2026-03-27
**Status:** Draft
**GitHub Issue:** #11
**Author:** Satheesh

---

## 1. Overview

The platform currently serves a single game: IPL Cluster 4 (Connections-style). The goal of this feature is to introduce a **multi-puzzle interface** that allows multiple independent puzzle games to coexist under one platform — beginning with the addition of a **Kerala Elections Edition** alongside the existing IPL Edition.

Users should be able to discover, navigate between, and play any available game from a unified entry point.

---

## 2. Goals

- Enable the platform to host games across multiple domains (Sports, Politics, etc.).
- Provide a **home screen** with visible, clickable game cards grouped by category.
- Provide a **burger/hamburger navigation menu** so users can switch games while mid-play.
- Add the **Kerala Elections puzzle** as the first non-sports game.
- Maintain backward compatibility: all existing IPL game functionality unchanged.
- Keep the platform statically hosted (GitHub Pages) — no server required.

---

## 3. Platform Categories & Games

### 3.1 Category Hierarchy

```
Platform
├── Sports
│   └── IPL Edition (existing — Cluster 4, Connections-style)
└── Politics
    └── Kerala Elections Edition (new)
```

Future categories (out of scope for this version):
- Entertainment, History, Geography, etc.

### 3.2 Game Registry

A central game registry defines all available games. Each entry includes:

| Field | Description | Example |
|---|---|---|
| `slug` | URL-safe unique ID | `"ipl"`, `"kerala-elections"` |
| `category` | Top-level grouping | `"Sports"`, `"Politics"` |
| `label` | Display name | `"IPL Edition"` |
| `description` | Short tagline | `"Group 16 IPL items into 4 categories"` |
| `icon` | Emoji or SVG icon | `"🏏"`, `"🗳️"` |
| `path` | URL route | `"/sports/ipl"`, `"/politics/kerala-elections"` |
| `status` | Visibility state | `"active"`, `"coming-soon"` |
| `puzzleDir` | Puzzle JSON directory | `"puzzles/ipl"`, `"puzzles/kerala-elections"` |

---

## 4. Navigation Requirements

### 4.1 Home Screen

- Displayed at the root path (`/`).
- Shows all registered games grouped by category.
- Each game is shown as a **card** with icon, label, description, and status badge.
- Active games: clicking a card navigates to the game.
- Coming-soon games: card is visible but non-interactive (greyed badge).
- Since there are initially few games, cards are displayed prominently (no collapse/accordion).

### 4.2 Burger Menu (In-Game Navigation)

- Accessible from the **Header** on any game page.
- Hamburger icon (☰) on the top-left or top-right of the header.
- Opens a **side drawer** (slides in from the left or right).
- Drawer content:
  - Platform logo / name at the top.
  - Categories as section headings.
  - Games listed under each category with icon + label.
  - Currently active game is visually highlighted.
  - "Home" link at the bottom.
- Drawer closes on: overlay click, Escape key, or selecting a game.
- Drawer is accessible: focus-trapped when open, ARIA roles applied.

### 4.3 Routing

- Use **HashRouter** (`/#/...`) for GitHub Pages compatibility (no server-side redirect required).
- Routes:
  - `/#/` → Home screen
  - `/#/sports/ipl` → IPL game
  - `/#/politics/kerala-elections` → Kerala Elections game
- Unknown routes → redirect to home.
- Visiting `/#/sports/ipl` directly (deep link) loads the IPL game without going to home first.

---

## 5. Kerala Elections Edition

### 5.1 Game Type

Uses the **same Connections puzzle format** as IPL Cluster 4:
- 16 items in a 4×4 grid.
- 4 categories of 4 items each, with color-coded difficulty.
- Client-side hash verification (same `hashItems()` function).
- Same game engine (`useGameEngine`) with a different puzzle slug.

### 5.2 Thematic Branding

| Element | IPL Edition | Kerala Elections Edition |
|---|---|---|
| Header title | "Cluster 4 - IPL Edition" | "Cluster 4 - Kerala Elections" |
| Header icon | Cricket ball 🏏 | Ballot box 🗳️ |
| Category colors | Yellow / Green / Blue / Purple | Same (difficulty scale) |
| Lives label | "Wickets" | "Chances" |
| Sharing header | "IPL Cluster 4 #N" | "Kerala Elections #N" |

### 5.3 Kerala Elections Content Examples

| Color | Difficulty | Example Category | Example Items |
|---|---|---|---|
| Yellow | Easiest | "Kerala Districts" | Thiruvananthapuram, Ernakulam, Kozhikode, Thrissur |
| Green | Moderate | "2021 UDF Winners" | — |
| Blue | Hard | "Ministers in Current Cabinet" | — |
| Purple | Hardest | "Election-related wordplay" | — |

### 5.4 Puzzle Directory

```
public/puzzles/
├── ipl/                  # existing
│   └── YYYY-MM-DD.json
└── kerala-elections/     # new
    └── YYYY-MM-DD.json
```

Puzzle JSON schema is identical to IPL. The `id` and `edition` fields are scoped per game.

---

## 6. Session & Storage Isolation

- Each game's localStorage keys are **prefixed with the game slug** to prevent state conflicts.
  - IPL: `ipl-cluster4-{puzzleId}` (existing key — unchanged for backward compatibility)
  - Kerala Elections: `kerala-elections-{puzzleId}`
- The "help seen" flag is also scoped per game:
  - IPL: `ipl-cluster4-help-seen` (unchanged)
  - Kerala Elections: `kerala-elections-help-seen`

---

## 7. UI / UX Requirements

### 7.1 Home Screen Layout

```
┌────────────────────────────────────────┐
│  [Platform Name / Logo]                │
│                                        │
│  Sports                                │
│  ┌──────────────────────────────────┐  │
│  │ 🏏  IPL Edition                  │  │
│  │     Group 16 IPL items into 4... │  │
│  │                          [Play →] │  │
│  └──────────────────────────────────┘  │
│                                        │
│  Politics                              │
│  ┌──────────────────────────────────┐  │
│  │ 🗳️  Kerala Elections Edition     │  │
│  │     Group 16 political items...  │  │
│  │                   [Coming Soon]  │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

### 7.2 Header (In-Game)

```
┌────────────────────────────────────────┐
│ ☰  🏏  IPL Edition   Edition 3 · Date ? │
└────────────────────────────────────────┘
```

- Burger icon on the left.
- Game icon + title in the center.
- Edition + date on the right (unchanged from current).
- Help "?" button retained.

### 7.3 Nav Drawer

```
┌──────────────────┐
│  🎮 Puzzle Games │
│                  │
│  Sports          │
│    🏏 IPL Edition│ ← active
│                  │
│  Politics        │
│  🗳️ Kerala Elec. │
│                  │
│  ─────────────── │
│  🏠 Home         │
└──────────────────┘
```

### 7.4 Responsive Design

- Home screen: single-column on mobile, 2-column grid on tablet+.
- Nav drawer: full-height, fixed-position overlay on all screen sizes.
- Mobile-first; all tap targets ≥ 48×48 px.

### 7.5 Accessibility

- Drawer: `role="dialog"`, `aria-modal="true"`, focus-trapped when open.
- Home cards: `role="link"` or `<a>` with descriptive `aria-label`.
- Coming-soon cards: `aria-disabled="true"`.
- Keyboard: Tab to navigate cards, Enter to open, Escape to close drawer.

---

## 8. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Routing | HashRouter for GitHub Pages compatibility |
| Bundle size | Adding router + home screen < 20 KB gzip overhead |
| No server changes | All routing and game logic is client-side only |
| Backward compatibility | Existing IPL game state in localStorage is unaffected |
| Deep-link support | Direct URL to any game loads correctly |

---

## 9. Out of Scope (v1)

- User accounts or cross-game statistics.
- Game search or filtering.
- Game-specific themes/color palettes (category colors remain universal).
- More than 2 games at launch.
- Admin UI to register new games (registry is code-managed).

---

## 10. Future Considerations

- Add more categories: Entertainment, Geography, History.
- Per-game custom difficulty color names (e.g., "Wickets" vs "Chances").
- Unified streak tracking across all games.
- Game-specific PWA manifest (separate app icons per game).
- Localization: Malayalam for Kerala Elections edition.
