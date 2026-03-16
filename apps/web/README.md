# IPL Connections — Web App

Daily IPL cricket word-association game built with React 18 + Vite + TypeScript + Tailwind CSS.

---

## Prerequisites

- **Node.js** 18+ (check with `node -v`)
- **npm** 9+ (comes with Node)

---

## Local Development

```bash
# From the repo root
cd apps/web

# Install dependencies (first time only, or after pulling new changes)
npm install

# Start the dev server with hot-module reload
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

The app loads today's puzzle from `public/puzzles/YYYY-MM-DD.json`. If no puzzle file exists
for today it will show an error — add a puzzle file to `public/puzzles/` to test locally
(see [puzzle curator docs](../../packages/puzzle-curator/README.md)).

---

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server at http://localhost:5173 |
| `npm run build` | TypeScript check + production build → `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run test` | Run tests once |
| `npm run test:watch` | Run tests in watch mode |
| `npm run lint` | Run ESLint |

---

## Project Structure

```
apps/web/
├── public/
│   ├── puzzles/          # Daily puzzle JSON files (YYYY-MM-DD.json)
│   └── favicon.svg       # Cricket ball favicon
├── src/
│   ├── components/       # React UI components
│   │   └── icons/        # Inline SVG icon components
│   ├── hooks/            # Custom React hooks (usePuzzle, useGameState)
│   ├── lib/              # Utilities (hash.ts — SHA-256 answer verification)
│   ├── types/            # TypeScript type definitions
│   ├── App.tsx           # Root component
│   └── main.tsx          # Entry point
├── tailwind.config.ts    # Theme colors (game.* + category.*)
└── vite.config.ts        # Vite config
```

---

## Adding a Puzzle for Local Testing

Generate a puzzle file using the curator tool and drop it into `public/puzzles/`:

```bash
cd packages/puzzle-curator
python auto_curator.py generate \
  --date $(date +%Y-%m-%d) \
  --output ../../apps/web/public/puzzles/ \
  --data-file ../data-pipeline/data/ipl_data.json \
  --categories yellow:orange_cap green:purple_cap blue:ipl_champions purple:team_players:CSK:2025
```

See [puzzle curator docs](../../packages/puzzle-curator/README.md) for full instructions.

---

## Production Build

```bash
npm run build
# Output in dist/ — deploy to GitHub Pages or any static host
```

The `npm run build` command runs TypeScript type checking first (`tsc -b`) and will fail
on type errors before bundling.
