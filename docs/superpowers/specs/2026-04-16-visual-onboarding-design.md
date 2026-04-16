# Visual Onboarding Design

**Date:** 2026-04-16  
**Branch:** feature/issue-15-game-mode  
**Problem:** Cold Facebook ad traffic lands on the game, sees a text-heavy help modal, and leaves before playing a single move.  
**Solution:** Three-layer visual onboarding that reduces reading friction and gets users into the game faster.

---

## Decisions Made

| Question | Decision |
|---|---|
| Approach | All three layers combined (improved modal + tooltip + persistent ?) |
| GIF format | User-recorded GIF (`help-demo.gif`) dropped into `apps/web/public/` |
| Modal layout | GIF hero on top, vertical stacked rules below, game mode comparison, colour key, CTA |
| Rules layout | Vertical stack with fuller text (icon + bold label + explanation) |
| Game mode placement | Side-by-side Easy vs Pro section inside the modal (replaces `GameModeTipModal` responsibility) |
| Primary target | Mobile (Facebook ad traffic, ~390px viewport) |

---

## Layer 1 — Improved Help Modal

**Trigger:** Auto-shows on first visit (existing `HELP_SEEN_KEY` logic, no change). Re-opens via `?` button in header anytime.

**Structure (top to bottom):**

1. **GIF hero** — `<img src="/help-demo.gif" autoplay loop>` at full modal width, ~110px tall. Shows: select tiles → submit → category banner reveals.
2. **4 vertical rules** — icon + bold label + plain-English explanation:
   - 👆 **Tap 4 players** — select items that share a common IPL theme
   - ✅ **Submit** — correct group revealed; wrong guess costs a life
   - 💡 **Hints** — reveal a category title to help narrow it down
   - 🏆 **Find all 4 groups** — IPL 2008–present, use Shuffle to spot connections
3. **Divider**
4. **Game Mode comparison** — side-by-side Easy vs Pro:
   - ⚡ Easy: 6 lives, 3 hints, wrong tile highlighted on "one away", "2 of 4" toast
   - 🏏 Pro: 4 lives, 2 hints, no extra guidance
   - Note: "Toggle in header · locks after your first guess"
5. **Colour difficulty key** — 4 coloured dots with "Yellow (easy) → Purple (hardest)" label
6. **"Let's Play!" CTA button**

**Changes to `HelpModal.tsx`:**
- Replace the `<ol>` rules list with 4 vertical icon-rows
- Add GIF `<img>` above the title (or replace title area)
- Add game mode section after rules, before difficulty key
- Remove `GameModeTipModal` auto-show from `App.tsx` (mode info now lives in the help modal)

---

## Layer 2 — Contextual Tooltip

**Trigger:** First tile tap ever (no prior `guessHistory`, no prior `revealedCategories`). Stored in localStorage key `ipl-cluster4-tooltip-seen`.

**Behaviour:**
- Renders a small bubble above the Submit button area: `"Tap 3 more players, then hit Submit →"`
- Auto-dismisses after 4 seconds OR on the user's next tap
- Shows once only — never again after dismissed

**New component:** `FirstTapTooltip.tsx` — simple absolute-positioned bubble, no animation library needed. Rendered inside `GameBoard.tsx` conditionally.

**State:** Managed in `GameBoard.tsx` via a `useState<boolean>` initialised from localStorage. Set to hidden on first tap after the tooltip has been shown.

---

## Layer 3 — Persistent "?" Button

Already implemented in `Header.tsx` via `onHelp` prop. **No changes required.**

---

## Files Changed

| File | Change |
|---|---|
| `apps/web/src/components/HelpModal.tsx` | Rewrite content: add GIF, vertical rules, game mode section |
| `apps/web/src/components/GameBoard.tsx` | Add `FirstTapTooltip` trigger logic |
| `apps/web/src/components/FirstTapTooltip.tsx` | New component |
| `apps/web/src/App.tsx` | Remove `GameModeTipModal` auto-show (mode info now in HelpModal) |
| `apps/web/public/help-demo.gif` | Drop in user-recorded GIF |

---

## Out of Scope

- Converting GIF to WebM (can be done later as a perf improvement)
- Animated CSS/JS demo (replaced by real GIF)
- Multi-step wizard modal
- Changes to game engine or puzzle logic
