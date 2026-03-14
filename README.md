# ipl_games

Word games for IPL, inspired by NYT games like Connections and Strands.

## Packages

| Package | Description |
|---------|-------------|
| `apps/web` | React frontend -- daily puzzle UI |
| `packages/data-pipeline` | IPL data pipeline -- loads and normalises data into SQLite + JSON |
| `packages/puzzle-curator` | CLI to create and validate daily puzzle JSON files |

## Data Pipeline

See [`packages/data-pipeline/README.md`](packages/data-pipeline/README.md) for how to load, clear, and update IPL data.

## Puzzle Curator

See [`packages/puzzle-curator/README.md`](packages/puzzle-curator/README.md) for how to create and validate puzzles.
