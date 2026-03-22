# Cluster4 — Platform Rebrand Requirements

**Spec Version:** 1.0
**Date:** 2026-03-16
**Status:** Draft

---

## 1. Overview

**Cluster4** is the umbrella platform name for a family of daily puzzle games built around sports knowledge. Each game targets a specific league or tournament (IPL, EPL, FIFA World Cup, etc.) and follows the same core mechanic: find 4 groups of 4 items sharing a common theme.

The current app ("IPL Connections") is being renamed **IPL Cluster 4** — the first game on the Cluster4 platform.

---

## 2. Goals

- Establish "Cluster4" as the recognisable brand across all games.
- Rename the IPL game from "IPL Connections" to "IPL Cluster 4" for brand consistency.
- Lay the naming foundation so future games (EPL Cluster 4, World Cup Cluster 4, etc.) fit naturally.
- Keep the rebrand purely cosmetic — no gameplay mechanics change.

---

## 3. Platform Vision

| Game | Sport / League | Status |
|------|---------------|--------|
| IPL Cluster 4 | Indian Premier League (cricket) | Active — rename from IPL Connections |
| EPL Cluster 4 | English Premier League (football) | Future |
| World Cup Cluster 4 | FIFA World Cup (football) | Future |

---

## 4. Naming Convention

- **Platform:** Cluster4
- **Game format:** `{League} Cluster 4` (e.g., "IPL Cluster 4")
- **Browser tab:** `{Game Name} — Cluster4` (e.g., "IPL Cluster 4 — Cluster4")

---

## 5. Scope of Changes for IPL Cluster 4 Rename

### 5.1 UI / Frontend (`apps/web/`)

| Location | Old Text | New Text |
|----------|----------|----------|
| `index.html` — `<title>` | `web` | `IPL Cluster 4 — Cluster4` |
| `Header.tsx` — h1 | `IPL Connections` | `IPL Cluster 4` |
| `HelpModal.tsx` — subtitle | `IPL Connections` | `IPL Cluster 4` |
| `GameBoard.tsx` — aria-label | `IPL Connections puzzle` | `IPL Cluster 4 puzzle` |

### 5.2 Storage Keys

| File | Old Key | New Key |
|------|---------|---------|
| `storage.ts` | `ipl-connections-{id}` | `ipl-cluster4-{id}` |
| `storage.ts` (prefix scan) | `ipl-connections-` | `ipl-cluster4-` |
| `App.tsx` | `ipl-connections-help-seen` | `ipl-cluster4-help-seen` |

> **Note:** Changing storage keys resets existing users' saved state (help-seen flag and puzzle progress). Acceptable at this stage.

### 5.3 Package Metadata

| File | Old Value | New Value |
|------|-----------|-----------|
| `apps/web/package.json` — `name` | `web` | `ipl-cluster4` |

### 5.4 Spec Files

- `specs/connections/requirements.md` — update all `IPL Connections` → `IPL Cluster 4`
- `specs/connections/implementation_plan.md` — update all `IPL Connections` → `IPL Cluster 4`

---

## 6. Out of Scope

- No gameplay mechanic changes.
- No new game pages or routing (future work when EPL / World Cup games are added).
- No logo or favicon changes in this iteration.
- No backend / data-pipeline renaming (internal identifiers can stay as-is).

---

## 7. Acceptance Criteria

- [ ] Browser tab shows "IPL Cluster 4 — Cluster4".
- [ ] App header shows "IPL Cluster 4".
- [ ] Help modal subtitle shows "IPL Cluster 4".
- [ ] LocalStorage keys use `ipl-cluster4-` prefix.
- [ ] No remaining `IPL Connections` or `ipl-connections` strings in `apps/web/src/`.
- [ ] Spec files (`specs/connections/`) updated to reflect new name.
