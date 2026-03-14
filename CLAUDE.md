# Introduction
Word games for IPL. This follow the similar style of NYtimes games such as connections and strands

# Architecture

UI interface which shows the daily puzzle, cookies or user session to store users daily session and results.
Backend contains a logic to generate a daily puzzle, store it in a static file, answer of the puzzle will hashed to send it with the puzzle so, no backend interation to verify the puzzle.
Data set generator to get data from various sources such as webscrapping, kaggle, cric api etc

# Project Structure

```
ipl_games/
├── apps/
│   └── web/                        # React 18 + Vite frontend
│       ├── src/                    # Components, hooks, game logic
│       ├── public/                 # Static assets, puzzle JSONs
│       └── dist/                   # Build output (deployed to GitHub Pages)
│
├── packages/
│   ├── data-pipeline/              # IPL data collection and loading (Python)
│   │   ├── kaggle_loader.py        # Loads Kaggle CSVs into SQLite
│   │   ├── squad_loader.py         # Loads ipl20??-squad CSV files
│   │   ├── normalizer.py           # Normalises DB, loads coaches, exports JSON
│   │   ├── espncricinfo.py         # Web scraper for recent seasons
│   │   ├── schema.py               # SQLite schema definitions
│   │   ├── data/                   # Input CSVs, manual JSON files, ipl.db, ipl_data.json
│   │   └── README.md               # Data pipeline usage guide → packages/data-pipeline/README.md
│   │
│   └── puzzle-curator/             # CLI tool to build daily puzzles (Python)
│       ├── curator.py              # Interactive puzzle builder
│       └── hash_util.py            # Answer hashing (matches browser Web Crypto)
│
├── specs/
│   └── connections/                # Spec-driven development docs
│       ├── requirements.md         # High-level requirements
│       └── implementation_plan.md  # Implementation plan
│
├── .github/workflows/              # GitHub Actions — deploy to GitHub Pages
├── CLAUDE.md                       # This file
└── README.md                       # Project overview
```

**Data pipeline details:** [packages/data-pipeline/README.md](packages/data-pipeline/README.md)

# Critical Info
- Follow spec-driven development (SDD). Specs stored in `specs/` directory with `requirements.md` and `implementation_plan.md`
- Any changes must update the spec before generating code
