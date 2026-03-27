# Multi-Puzzle Interface — Implementation Plan

**Spec Version:** 1.0
**Date:** 2026-03-27
**Status:** Draft
**References:** `specs/multi-puzzle/requirements.md`, `specs/connections/implementation_plan.md`
**GitHub Issue:** #11

---

## 1. Tech Stack Additions

| Addition | Choice | Rationale |
|---|---|---|
| Routing | `react-router-dom` v6 | Standard, well-documented, works with HashRouter for GitHub Pages |
| Router type | `HashRouter` | No server config needed; GitHub Pages serves `index.html` only at root |

No other new dependencies are required. The existing React + Vite + TypeScript + Tailwind stack is sufficient.

---

## 2. New File Structure

```
apps/web/src/
├── games.ts                          # NEW — central game registry
├── pages/
│   ├── HomePage.tsx                  # NEW — landing page with game cards
│   └── GamePage.tsx                  # NEW — wraps existing App logic, reads slug from route
├── components/
│   ├── NavDrawer.tsx                 # NEW — burger menu side drawer
│   ├── GameCard.tsx                  # NEW — game card for home screen
│   └── Header.tsx                   # MODIFIED — add burger icon, accept game config prop
├── hooks/
│   └── usePuzzle.ts                  # MODIFIED — accept gameSlug param
└── App.tsx                           # MODIFIED — add router + routes, remove direct puzzle load

apps/web/public/puzzles/
├── ipl/                              # existing (unchanged)
└── kerala-elections/                 # NEW — empty dir with .gitkeep
    └── .gitkeep
```

---

## 3. Game Registry (`src/games.ts`)

Central source of truth for all games. New games are added here only.

```typescript
export interface GameConfig {
  slug: string;
  category: string;
  label: string;
  description: string;
  icon: string;
  path: string;
  status: 'active' | 'coming-soon';
  puzzleDir: string;
  storagePrefix: string;
}

export const GAMES: GameConfig[] = [
  {
    slug: 'ipl',
    category: 'Sports',
    label: 'IPL Edition',
    description: 'Group 16 IPL cricket items into 4 hidden categories.',
    icon: '🏏',
    path: '/sports/ipl',
    status: 'active',
    puzzleDir: 'puzzles/ipl',
    storagePrefix: 'ipl-cluster4',   // preserves existing localStorage keys
  },
  {
    slug: 'kerala-elections',
    category: 'Politics',
    label: 'Kerala Elections Edition',
    description: 'Group 16 Kerala politics items into 4 hidden categories.',
    icon: '🗳️',
    path: '/politics/kerala-elections',
    status: 'coming-soon',
    puzzleDir: 'puzzles/kerala-elections',
    storagePrefix: 'kerala-elections',
  },
];

// Group games by category for display
export function getGamesByCategory(): Record<string, GameConfig[]> {
  return GAMES.reduce((acc, game) => {
    (acc[game.category] ??= []).push(game);
    return acc;
  }, {} as Record<string, GameConfig[]>);
}

export function getGameBySlug(slug: string): GameConfig | undefined {
  return GAMES.find(g => g.slug === slug);
}
```

---

## 4. Routing Setup (`src/App.tsx`)

Replace the current single-puzzle `App.tsx` render with a router.

```tsx
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import GamePage from './pages/GamePage';

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/sports/ipl" element={<GamePage slug="ipl" />} />
        <Route path="/politics/kerala-elections" element={<GamePage slug="kerala-elections" />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  );
}
```

---

## 5. Home Page (`src/pages/HomePage.tsx`)

```tsx
import { getGamesByCategory } from '../games';
import GameCard from '../components/GameCard';

export default function HomePage() {
  const byCategory = getGamesByCategory();
  return (
    <div className="min-h-screen bg-[#1a1a2e] text-white p-4 max-w-2xl mx-auto">
      <header className="text-center py-8">
        <h1 className="text-3xl font-bold">Puzzle Games</h1>
        <p className="text-gray-400 mt-1">Daily puzzles across sports, politics & more</p>
      </header>
      {Object.entries(byCategory).map(([category, games]) => (
        <section key={category} className="mb-8">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-400 mb-3">
            {category}
          </h2>
          <div className="flex flex-col gap-3">
            {games.map(game => <GameCard key={game.slug} game={game} />)}
          </div>
        </section>
      ))}
    </div>
  );
}
```

---

## 6. Game Card (`src/components/GameCard.tsx`)

```tsx
import { Link } from 'react-router-dom';
import { GameConfig } from '../games';

export default function GameCard({ game }: { game: GameConfig }) {
  const isActive = game.status === 'active';
  return (
    <div className={`rounded-xl border p-4 flex items-center gap-4 ${
      isActive ? 'border-white/20 bg-white/5 hover:bg-white/10 cursor-pointer'
               : 'border-white/10 bg-white/[0.02] opacity-60'
    }`}>
      <span className="text-3xl">{game.icon}</span>
      <div className="flex-1">
        <div className="font-semibold">{game.label}</div>
        <div className="text-sm text-gray-400">{game.description}</div>
      </div>
      {isActive ? (
        <Link
          to={game.path}
          className="text-sm font-medium px-3 py-1 rounded-full bg-white/10 hover:bg-white/20"
          aria-label={`Play ${game.label}`}
        >
          Play →
        </Link>
      ) : (
        <span className="text-xs px-2 py-1 rounded-full bg-white/5 text-gray-500">
          Coming Soon
        </span>
      )}
    </div>
  );
}
```

---

## 7. Game Page (`src/pages/GamePage.tsx`)

Wraps the existing game UI. Reads the game config by slug and passes it down.

```tsx
import { getGameBySlug } from '../games';
import { usePuzzle } from '../hooks/usePuzzle';
import Header from '../components/Header';
import GameBoard from '../components/GameBoard';
import HelpModal from '../components/HelpModal';
import { useState, useEffect } from 'react';

export default function GamePage({ slug }: { slug: string }) {
  const game = getGameBySlug(slug)!;
  const { puzzle, loading, error } = usePuzzle(game.puzzleDir);
  const helpSeenKey = `${game.storagePrefix}-help-seen`;
  const [showHelp, setShowHelp] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem(helpSeenKey)) {
      setShowHelp(true);
      localStorage.setItem(helpSeenKey, 'true');
    }
  }, [helpSeenKey]);

  if (loading) return <div className="...">Loading...</div>;
  if (error || !puzzle) return <div className="...">Error loading puzzle.</div>;

  return (
    <div className="min-h-screen bg-[#1a1a2e] text-white flex flex-col">
      <Header
        game={game}
        edition={puzzle.edition}
        date={puzzle.date}
        onHelpClick={() => setShowHelp(true)}
      />
      {showHelp && <HelpModal onClose={() => setShowHelp(false)} />}
      <GameBoard puzzle={puzzle} storagePrefix={game.storagePrefix} />
    </div>
  );
}
```

---

## 8. Modified: `usePuzzle` Hook

Accept a `puzzleDir` param instead of hardcoding the path.

```typescript
// Before
const url = `${BASE_URL}puzzles/ipl/${dateStr}.json`;

// After
export function usePuzzle(puzzleDir: string) {
  // ...
  const url = `${BASE_URL}${puzzleDir}/${dateStr}.json`;
  const fallback = `${BASE_URL}${puzzleDir}/dev.json`;
  // rest unchanged
}
```

---

## 9. Modified: `Header` Component

Add burger menu button; accept `game` config prop instead of hardcoded strings.

```tsx
// Props change:
// Before: { edition, date, onHelpClick }
// After:  { game, edition, date, onHelpClick, onMenuClick }

export default function Header({ game, edition, date, onHelpClick, onMenuClick }) {
  return (
    <header className="...">
      <button onClick={onMenuClick} aria-label="Open menu">☰</button>
      <div className="flex items-center gap-2">
        <span>{game.icon}</span>
        <span>{game.label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span>Edition {edition} · {formatDate(date)}</span>
        <button onClick={onHelpClick} aria-label="Help">?</button>
      </div>
    </header>
  );
}
```

---

## 10. Nav Drawer (`src/components/NavDrawer.tsx`)

```tsx
import { Link, useLocation } from 'react-router-dom';
import { GAMES, getGamesByCategory } from '../games';

export default function NavDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const location = useLocation();
  const byCategory = getGamesByCategory();

  // Trap focus when open; close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} aria-hidden />
      {/* Drawer */}
      <nav
        className="fixed top-0 left-0 h-full w-64 bg-[#1a1a2e] border-r border-white/10 z-50 p-4 flex flex-col"
        role="dialog"
        aria-modal="true"
        aria-label="Game navigation"
      >
        <div className="font-bold text-lg mb-6">🎮 Puzzle Games</div>
        {Object.entries(byCategory).map(([category, games]) => (
          <div key={category} className="mb-4">
            <div className="text-xs uppercase tracking-widest text-gray-400 mb-2">{category}</div>
            {games.map(game => (
              <Link
                key={game.slug}
                to={game.path}
                onClick={onClose}
                className={`flex items-center gap-2 px-2 py-2 rounded-lg text-sm mb-1 ${
                  location.pathname === game.path ? 'bg-white/15 font-semibold' : 'hover:bg-white/10'
                }`}
              >
                {game.icon} {game.label}
                {game.status === 'coming-soon' && (
                  <span className="ml-auto text-xs text-gray-500">Soon</span>
                )}
              </Link>
            ))}
          </div>
        ))}
        <div className="mt-auto border-t border-white/10 pt-4">
          <Link to="/" onClick={onClose} className="flex items-center gap-2 text-sm hover:text-white text-gray-400">
            🏠 Home
          </Link>
        </div>
      </nav>
    </>
  );
}
```

---

## 11. `GameBoard` — Storage Key Scoping

Pass `storagePrefix` from `GamePage` down to `GameBoard`, and thread it into `useGameEngine` / `lib/storage.ts`.

```typescript
// lib/storage.ts
// Before: hardcoded prefix
const KEY = (id: string) => `ipl-cluster4-${id}`;

// After: prefix passed as param
export const storageKey = (prefix: string, id: string) => `${prefix}-${id}`;
```

The IPL prefix remains `'ipl-cluster4'` — existing user state is unaffected.

---

## 12. Puzzle Directory Setup

```
public/puzzles/kerala-elections/
└── .gitkeep       # placeholder so directory is committed
```

A `dev.json` for Kerala Elections is created for local development when puzzle curation begins.

---

## 13. Implementation Phases

### Phase 1 — Routing Foundation ✅
- [x] Install `react-router-dom`
- [x] Create `src/games.ts` with registry
- [x] Refactor `src/App.tsx` to use `HashRouter` + `Routes`
- [x] Create `src/pages/HomePage.tsx` and `src/components/GameCard.tsx`
- [x] Create `src/pages/GamePage.tsx` (thin wrapper)
- [x] Verify existing IPL game still works at `/#/sports/ipl`

### Phase 2 — Generalized Game Loading ✅
- [x] Update `usePuzzle` to accept `puzzleDir` param
- [x] Pass `storagePrefix` from `GamePage` → `GameBoard` → `useGameEngine`
- [x] Update `lib/storage.ts` to accept prefix param
- [x] Verify IPL localStorage keys unchanged (`ipl-cluster4-*`)

### Phase 3 — Header & Nav Drawer ✅
- [x] Update `Header.tsx` props: accept `game` config, add burger button
- [x] Create `NavDrawer.tsx` with focus-trap, Escape key, overlay dismiss
- [x] Wire `NavDrawer` open/close state in `GamePage`
- [x] Accessibility audit: ARIA roles, focus management

### Phase 4 — Kerala Elections Scaffold ✅
- [x] Create `public/puzzles/kerala-elections/` with `.gitkeep`
- [x] Create `public/puzzles/kerala-elections/dev.json` (sample puzzle for local dev)
- [x] Set `status: 'coming-soon'` in registry until first real puzzle is curated

### Phase 5 — Game-Aware Components & Polish

#### 5a — Lives Indicator (generic circles) ✅
- [x] Remove cricket wicket icon; replace with filled/empty circle dots
  - Filled circle `●` = life remaining; greyed circle `○` = life lost
  - Label changes from "Wickets remaining" to "Lives remaining" for all games
  - `LivesIndicator` requires no game prop — circles are universal
  - Update `aria-label` from `N wicket(s) remaining` → `N life/lives remaining`

#### 5b — Help Modal (game-aware content) ✅
- [x] Accept `game: GameConfig` prop; derive title and descriptions from it
- [x] Replace hardcoded `"Cluster 4 - IPL Edition"` subtitle with `game.label`
- [x] Replace hardcoded IPL tagline with `tagline` field per game in `games.ts`
- [x] Replace IPL-specific difficulty examples with generic ones
- [x] Pass `game` from `GamePage` → `HelpModal`

#### 5c — Results Modal (game-aware share text) ✅
- [x] Accept `game: GameConfig` prop
- [x] Replace hardcoded `"Cluster 4 – IPL #N"` header with `"Cluster 4 – ${game.label} #N"`
- [x] Replace hardcoded `"Cluster 4 · IPL #N"` subtitle with `"${game.label} #N"`
- [x] Pass `game` from `GamePage` → `GameBoard` → `ResultsModal`

#### 5d — Remaining Polish
- [ ] Home screen responsive layout (mobile single-column, tablet 2-column)
- [ ] Smooth drawer animation (CSS transition or Framer Motion)
- [ ] Update PWA manifest name to reflect platform (not just "IPL")
- [ ] Test deep links: `/#/sports/ipl` and `/#/politics/kerala-elections`
- [ ] Test existing IPL game state not reset by this change
- [ ] Cross-browser check (Chrome, Safari, Firefox)

---

## 14. Testing Checklist

| Test | Expected |
|---|---|
| Visit `/#/` | Home screen shows both game cards |
| Click IPL card | Navigates to `/#/sports/ipl`, game loads |
| Kerala card (coming-soon) | Card is visible but "Play" button is absent |
| Deep-link to `/#/sports/ipl` | Game loads without visiting home |
| Unknown route `/#/foo` | Redirects to `/#/` |
| Open burger menu | Drawer slides in with correct active state |
| Close drawer via Escape | Drawer closes, focus returns to burger button |
| Close drawer via overlay | Drawer closes |
| Existing IPL localStorage | Not cleared by upgrade — game resumes correctly |
| New Kerala game | Uses separate `kerala-elections-*` keys |

---

## 15. Open Questions

| # | Question | Default Assumption |
|---|---|---|
| 1 | Should the platform have a name distinct from "IPL Games"? | Use "Puzzle Games" as placeholder; decide before launch |
| 2 | Should coming-soon games be hidden entirely or shown greyed? | Shown greyed — creates anticipation |
| 3 | Should `/#/sports/ipl` redirect to `/#/` when puzzle is unavailable? | No — show existing error state ("No puzzle today") |
| 4 | When Kerala Elections goes live, should it auto-show today's puzzle like IPL? | Yes — same date-based loading logic |
