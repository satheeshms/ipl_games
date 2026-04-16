# Visual Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the text-heavy help modal with a GIF-led visual onboarding experience, add a first-tap contextual tooltip, and surface Easy/Pro mode info inside the modal.

**Architecture:** Three independent changes — (1) rewrite `HelpModal.tsx` with GIF hero + game mode section, (2) new `FirstTapTooltip.tsx` component wired into `GameBoard.tsx`, (3) remove now-redundant `GameModeTipModal` auto-show from `App.tsx`. Each change is independently committable.

**Tech Stack:** React 19, TypeScript, Tailwind CSS, Framer Motion (already installed), Vitest + Testing Library.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `apps/web/public/help-demo.gif` | Drop in | User-recorded GIF asset |
| `apps/web/src/components/HelpModal.tsx` | Modify | GIF hero, vertical rules, Easy/Pro section |
| `apps/web/src/components/FirstTapTooltip.tsx` | Create | One-time tooltip bubble on first tile tap |
| `apps/web/src/components/GameBoard.tsx` | Modify | Render tooltip, trigger on first tile select |
| `apps/web/src/App.tsx` | Modify | Remove `GameModeTipModal` auto-show logic |
| `apps/web/src/test/HelpModal.test.tsx` | Create | Tests for new modal content |
| `apps/web/src/test/FirstTapTooltip.test.tsx` | Create | Tests for tooltip behaviour |

---

## Task 1: Drop the GIF asset

**Files:**
- Add: `apps/web/public/help-demo.gif`

- [ ] **Step 1: Copy the GIF**

  Move or copy your recorded `help-demo.gif` into `apps/web/public/help-demo.gif`.

- [ ] **Step 2: Verify it serves correctly**

  ```bash
  cd apps/web && npm run dev
  ```

  Open `http://localhost:5173/help-demo.gif` in the browser. You should see the GIF playing.

- [ ] **Step 3: Commit**

  ```bash
  git add apps/web/public/help-demo.gif
  git commit -m "feat: add help demo GIF asset"
  ```

---

## Task 2: Rewrite HelpModal with GIF hero and game mode section

**Files:**
- Modify: `apps/web/src/components/HelpModal.tsx`
- Create: `apps/web/src/test/HelpModal.test.tsx`

- [ ] **Step 1: Write the failing tests**

  Create `apps/web/src/test/HelpModal.test.tsx`:

  ```tsx
  import { describe, it, expect, vi } from 'vitest';
  import { render, screen } from '@testing-library/react';
  import userEvent from '@testing-library/user-event';
  import { HelpModal } from '../components/HelpModal';

  describe('HelpModal', () => {
    it('renders the GIF demo image', () => {
      render(<HelpModal onClose={() => {}} />);
      const img = screen.getByRole('img', { name: /how to play demo/i });
      expect(img).toHaveAttribute('src', '/help-demo.gif');
    });

    it('renders all four rules', () => {
      render(<HelpModal onClose={() => {}} />);
      expect(screen.getByText(/tap 4 players/i)).toBeInTheDocument();
      expect(screen.getByText(/submit/i)).toBeInTheDocument();
      expect(screen.getByText(/hints/i)).toBeInTheDocument();
      expect(screen.getByText(/find all 4 groups/i)).toBeInTheDocument();
    });

    it('shows correct Easy mode stats', () => {
      render(<HelpModal onClose={() => {}} />);
      expect(screen.getByText(/6 lives/i)).toBeInTheDocument();
      expect(screen.getByText(/3 hints/i)).toBeInTheDocument();
    });

    it('shows correct Pro mode stats', () => {
      render(<HelpModal onClose={() => {}} />);
      expect(screen.getByText(/4 lives/i)).toBeInTheDocument();
      expect(screen.getByText(/2 hints/i)).toBeInTheDocument();
    });

    it('calls onClose when Let\'s Play button is clicked', async () => {
      const onClose = vi.fn();
      render(<HelpModal onClose={onClose} />);
      await userEvent.click(screen.getByRole('button', { name: /let's play/i }));
      expect(onClose).toHaveBeenCalledOnce();
    });

    it('calls onClose when Escape key is pressed', async () => {
      const onClose = vi.fn();
      render(<HelpModal onClose={onClose} />);
      await userEvent.keyboard('{Escape}');
      expect(onClose).toHaveBeenCalledOnce();
    });
  });
  ```

- [ ] **Step 2: Run tests to verify they fail**

  ```bash
  cd apps/web && npm test -- HelpModal
  ```

  Expected: several FAIL — `getByRole('img')` not found, `6 lives` not found, `3 hints` not found.

- [ ] **Step 3: Rewrite HelpModal.tsx**

  Replace the entire contents of `apps/web/src/components/HelpModal.tsx`:

  ```tsx
  import { useEffect, useRef } from 'react';
  import { AnimatePresence, motion } from 'framer-motion';

  interface HelpModalProps {
    onClose: () => void;
  }

  const RULES = [
    {
      icon: '👆',
      label: 'Tap 4 players',
      detail: 'Select items from the grid that share a common IPL theme',
    },
    {
      icon: '✅',
      label: 'Submit',
      detail: 'Correct group is revealed with its title; wrong guess costs a life',
    },
    {
      icon: '💡',
      label: 'Hints',
      detail: 'Reveal a category title to help narrow it down',
    },
    {
      icon: '🏆',
      label: 'Find all 4 groups',
      detail: 'Puzzles span IPL 2008–present. Use Shuffle to spot connections',
    },
  ];

  const EASY_FEATURES = [
    '❤️ 6 lives',
    '💡 3 hints',
    '🎯 Wrong tile highlighted on "one away"',
    '📊 Tells you if 2 picks match',
  ];

  const PRO_FEATURES = [
    '❤️ 4 lives',
    '💡 2 hints',
    '🔕 No extra guidance',
    '💪 For the purists',
  ];

  const DIFFICULTY_DOTS = [
    { color: '#F9DF6D', label: 'Yellow — Easiest' },
    { color: '#A0C35A', label: 'Green — Moderate' },
    { color: '#B0C4EF', label: 'Blue — Hard' },
    { color: '#BA81C5', label: 'Purple — Hardest' },
  ];

  export function HelpModal({ onClose }: HelpModalProps) {
    const closeRef = useRef<HTMLButtonElement>(null);

    useEffect(() => {
      closeRef.current?.focus();
    }, []);

    useEffect(() => {
      function onKey(e: KeyboardEvent) {
        if (e.key === 'Escape') onClose();
      }
      window.addEventListener('keydown', onKey);
      return () => window.removeEventListener('keydown', onKey);
    }, [onClose]);

    return (
      <AnimatePresence>
        <motion.div
          key="backdrop"
          className="fixed inset-0 bg-black/70 z-40 overflow-y-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <div className="flex min-h-full items-center justify-center px-4 py-4">
            <motion.div
              key="panel"
              role="dialog"
              aria-modal="true"
              aria-labelledby="help-modal-title"
              className="relative bg-[#1a1a2e] border border-white/10 rounded-2xl w-full max-w-md p-6 z-50 text-white"
              initial={{ opacity: 0, y: 24, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 16, scale: 0.97 }}
              transition={{ type: 'spring', stiffness: 320, damping: 28 }}
              onClick={e => e.stopPropagation()}
            >
              {/* Close button */}
              <button
                ref={closeRef}
                onClick={onClose}
                aria-label="Close instructions"
                className="absolute top-4 right-4 text-white/60 hover:text-white transition-colors text-xl leading-none focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50 rounded"
              >
                ✕
              </button>

              <h2
                id="help-modal-title"
                className="text-xl font-bold text-center mb-1"
              >
                How to Play
              </h2>
              <p className="text-white/40 text-xs text-center mb-4">
                Cluster 4 - IPL Edition
              </p>

              {/* GIF hero */}
              <img
                src="/help-demo.gif"
                alt="How to play demo"
                className="w-full rounded-xl mb-5 border border-white/10"
                style={{ maxHeight: '160px', objectFit: 'cover' }}
              />

              {/* Vertical rules */}
              <div className="space-y-2 mb-5">
                {RULES.map(({ icon, label, detail }) => (
                  <div
                    key={label}
                    className="flex items-start gap-3 bg-white/5 rounded-lg px-3 py-2.5"
                  >
                    <span className="text-lg leading-none mt-0.5 shrink-0">{icon}</span>
                    <span className="text-sm leading-snug">
                      <strong>{label}</strong>
                      <span className="text-white/55"> — {detail}</span>
                    </span>
                  </div>
                ))}
              </div>

              {/* Game mode comparison */}
              <div className="border-t border-white/10 pt-4 mb-4">
                <p className="text-xs text-white/40 uppercase tracking-widest mb-3">
                  Choose your mode
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {/* Easy */}
                  <div className="rounded-lg p-3 bg-amber-400/10 border border-amber-400/30">
                    <p className="text-xs font-bold text-amber-300 mb-2">⚡ Easy</p>
                    <ul className="space-y-1">
                      {EASY_FEATURES.map(f => (
                        <li key={f} className="text-xs text-white/70 leading-snug">{f}</li>
                      ))}
                    </ul>
                  </div>
                  {/* Pro */}
                  <div className="rounded-lg p-3 bg-white/5 border border-white/10">
                    <p className="text-xs font-bold text-white/70 mb-2">🏏 Pro</p>
                    <ul className="space-y-1">
                      {PRO_FEATURES.map(f => (
                        <li key={f} className="text-xs text-white/70 leading-snug">{f}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                <p className="text-xs text-white/30 text-center mt-2">
                  Toggle in header · locks after your first guess
                </p>
              </div>

              {/* Difficulty colour key */}
              <div className="border-t border-white/10 pt-4 mb-5">
                <p className="text-xs text-white/40 uppercase tracking-widest mb-2">
                  Difficulty
                </p>
                <div className="flex items-center gap-2 flex-wrap">
                  {DIFFICULTY_DOTS.map(({ color, label }) => (
                    <div key={label} className="flex items-center gap-1.5">
                      <span
                        className="w-3.5 h-3.5 rounded-sm shrink-0"
                        style={{ backgroundColor: color }}
                      />
                      <span className="text-xs text-white/50">{label}</span>
                    </div>
                  ))}
                </div>
              </div>

              <button
                onClick={onClose}
                className="w-full bg-white text-[#1a1a2e] font-semibold rounded-full py-2.5 text-sm hover:bg-white/90 transition-colors"
              >
                Let's Play!
              </button>
            </motion.div>
          </div>
        </motion.div>
      </AnimatePresence>
    );
  }
  ```

- [ ] **Step 4: Run tests to verify they pass**

  ```bash
  cd apps/web && npm test -- HelpModal
  ```

  Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add apps/web/src/components/HelpModal.tsx apps/web/src/test/HelpModal.test.tsx
  git commit -m "feat: rewrite HelpModal with GIF hero and Easy/Pro mode section"
  ```

---

## Task 3: Create FirstTapTooltip component

**Files:**
- Create: `apps/web/src/components/FirstTapTooltip.tsx`
- Create: `apps/web/src/test/FirstTapTooltip.test.tsx`

- [ ] **Step 1: Write the failing tests**

  Create `apps/web/src/test/FirstTapTooltip.test.tsx`:

  ```tsx
  import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
  import { render, screen, act } from '@testing-library/react';
  import userEvent from '@testing-library/user-event';
  import { FirstTapTooltip } from '../components/FirstTapTooltip';

  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('FirstTapTooltip', () => {
    it('renders tooltip text when visible', () => {
      render(<FirstTapTooltip visible onDismiss={() => {}} />);
      expect(screen.getByText(/tap 3 more/i)).toBeInTheDocument();
    });

    it('renders nothing when not visible', () => {
      const { container } = render(<FirstTapTooltip visible={false} onDismiss={() => {}} />);
      expect(container.firstChild).toBeNull();
    });

    it('calls onDismiss after 4 seconds', () => {
      const onDismiss = vi.fn();
      render(<FirstTapTooltip visible onDismiss={onDismiss} />);
      expect(onDismiss).not.toHaveBeenCalled();
      act(() => { vi.advanceTimersByTime(4000); });
      expect(onDismiss).toHaveBeenCalledOnce();
    });

    it('calls onDismiss when clicked', async () => {
      const onDismiss = vi.fn();
      render(<FirstTapTooltip visible onDismiss={onDismiss} />);
      await userEvent.click(screen.getByRole('button', { name: /dismiss/i }));
      expect(onDismiss).toHaveBeenCalledOnce();
    });
  });
  ```

- [ ] **Step 2: Run tests to verify they fail**

  ```bash
  cd apps/web && npm test -- FirstTapTooltip
  ```

  Expected: FAIL — `FirstTapTooltip` not found.

- [ ] **Step 3: Create FirstTapTooltip.tsx**

  Create `apps/web/src/components/FirstTapTooltip.tsx`:

  ```tsx
  import { useEffect } from 'react';

  interface FirstTapTooltipProps {
    visible: boolean;
    onDismiss: () => void;
  }

  const AUTO_DISMISS_MS = 4000;

  export function FirstTapTooltip({ visible, onDismiss }: FirstTapTooltipProps) {
    useEffect(() => {
      if (!visible) return;
      const timer = setTimeout(onDismiss, AUTO_DISMISS_MS);
      return () => clearTimeout(timer);
    }, [visible, onDismiss]);

    if (!visible) return null;

    return (
      <div className="relative flex justify-start pl-2 mt-1">
        {/* Arrow pointing up */}
        <div className="absolute -top-2 left-6 w-0 h-0 border-l-[6px] border-r-[6px] border-b-[8px] border-l-transparent border-r-transparent border-b-white" />
        <button
          onClick={onDismiss}
          aria-label="Dismiss tip"
          className="bg-white text-[#1a1a2e] text-xs font-semibold rounded-lg px-3 py-2 shadow-lg leading-snug text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50"
        >
          Tap 3 more players, then hit <strong>Submit</strong> →
        </button>
      </div>
    );
  }
  ```

- [ ] **Step 4: Run tests to verify they pass**

  ```bash
  cd apps/web && npm test -- FirstTapTooltip
  ```

  Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add apps/web/src/components/FirstTapTooltip.tsx apps/web/src/test/FirstTapTooltip.test.tsx
  git commit -m "feat: add FirstTapTooltip component"
  ```

---

## Task 4: Wire FirstTapTooltip into GameBoard

**Files:**
- Modify: `apps/web/src/components/GameBoard.tsx`

- [ ] **Step 1: Add tooltip state and logic to GameBoard**

  At the top of `GameBoard.tsx`, after the existing imports, add:

  ```tsx
  import { FirstTapTooltip } from './FirstTapTooltip';
  ```

  Inside `GameBoard` function, after the existing `useState` declarations (around line 76), add:

  ```tsx
  const TOOLTIP_SEEN_KEY = 'ipl-cluster4-tooltip-seen';
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const tooltipShown = useRef(false);
  ```

  After the existing `selectItem` logic in `useGameEngine`, add a `useEffect` that triggers the tooltip on the first tile tap. Add this after the existing `useEffect` for puzzle loading (around line 88):

  ```tsx
  // Show first-tap tooltip once ever
  useEffect(() => {
    const alreadySeen = (() => {
      try { return !!localStorage.getItem(TOOLTIP_SEEN_KEY); } catch { return true; }
    })();
    if (
      !alreadySeen &&
      !tooltipShown.current &&
      state.selected.length === 1 &&
      state.guessHistory.length === 0 &&
      state.revealedCategories.length === 0
    ) {
      tooltipShown.current = true;
      setTooltipVisible(true);
    }
  }, [state.selected.length, state.guessHistory.length, state.revealedCategories.length]);

  const handleDismissTooltip = useCallback(() => {
    setTooltipVisible(false);
    try { localStorage.setItem(TOOLTIP_SEEN_KEY, '1'); } catch { /* ignore */ }
  }, []);
  ```

- [ ] **Step 2: Render the tooltip in the JSX**

  In the `GameBoard` return JSX, find the `<ActionBar ... />` block (around line 292). Add `<FirstTapTooltip>` immediately above it:

  ```tsx
  {/* First-tap onboarding tooltip */}
  <FirstTapTooltip visible={tooltipVisible} onDismiss={handleDismissTooltip} />

  <ActionBar
    onShuffle={engine.shuffle}
    onDeselectAll={engine.deselectAll}
    onSubmit={handleSubmit}
    onHint={handleHint}
    onShare={handleShareResult}
    canSubmit={state.selected.length === 4 && state.status === 'playing'}
    canDeselectAll={state.selected.length > 0}
    hintsRemaining={hintsRemaining}
    canHint={canHint}
    isGameOver={isGameOver && modalClosed}
  />
  ```

- [ ] **Step 3: Run the full test suite**

  ```bash
  cd apps/web && npm test
  ```

  Expected: all tests PASS (no new tests needed — behaviour is covered by `FirstTapTooltip.test.tsx`).

- [ ] **Step 4: Commit**

  ```bash
  git add apps/web/src/components/GameBoard.tsx
  git commit -m "feat: wire first-tap tooltip into GameBoard"
  ```

---

## Task 5: Remove GameModeTipModal auto-show from App.tsx

Now that Easy/Pro info lives in the help modal, the `GameModeTipModal` auto-show is redundant. The component itself can stay for now (it's still accessible if needed), but the auto-show logic should be removed.

**Files:**
- Modify: `apps/web/src/App.tsx`

- [ ] **Step 1: Remove auto-show state and logic**

  In `App.tsx`, remove these constants and all code that references them:

  ```tsx
  // REMOVE these lines:
  const MODE_TIP_COUNT_KEY = 'ipl-cluster4-mode-tip-count';
  const MODE_TIP_MAX = 3;

  function getModeTipCount(): number { ... }
  function incrementModeTipCount(): void { ... }
  ```

  Remove the `showModeTip` state:
  ```tsx
  // REMOVE:
  const [showModeTip, setShowModeTip] = useState(false);
  const modeTipShownThisSession = useRef(false);
  ```

  Remove the `useEffect` that auto-shows the mode tip:
  ```tsx
  // REMOVE this entire useEffect:
  useEffect(() => {
    if (!loading && puzzle && localStorage.getItem(HELP_SEEN_KEY)) {
      if (!modeTipShownThisSession.current && getModeTipCount() < MODE_TIP_MAX) {
        incrementModeTipCount();
        modeTipShownThisSession.current = true;
        setShowModeTip(true);
      }
    }
  }, [loading, puzzle]);
  ```

  In `closeHelp()`, remove the mode tip trigger block:
  ```tsx
  // REMOVE from closeHelp():
  if (!modeTipShownThisSession.current && getModeTipCount() < MODE_TIP_MAX) {
    incrementModeTipCount();
    modeTipShownThisSession.current = true;
    setShowModeTip(true);
  }
  ```

  Remove `closeModeTip` function:
  ```tsx
  // REMOVE:
  function closeModeTip() {
    setShowModeTip(false);
  }
  ```

  Remove the `GameModeTipModal` render and import:
  ```tsx
  // REMOVE from JSX:
  {showModeTip && <GameModeTipModal onClose={closeModeTip} />}

  // REMOVE import:
  import { GameModeTipModal } from './components/GameModeTipModal';
  ```

- [ ] **Step 2: Run the full test suite**

  ```bash
  cd apps/web && npm test
  ```

  Expected: all tests PASS.

- [ ] **Step 3: Run the dev server and verify manually**

  ```bash
  cd apps/web && npm run dev
  ```

  Check:
  - [ ] First visit: help modal auto-shows with GIF, rules, Easy/Pro section
  - [ ] Click "Let's Play!": modal closes, no second modal appears
  - [ ] Tap a tile: tooltip appears above the Submit button area
  - [ ] Tooltip auto-dismisses after 4 seconds (or tap to dismiss)
  - [ ] Reload: no tooltip (localStorage flag set), no mode tip modal
  - [ ] Click `?` in header: help modal re-opens

- [ ] **Step 4: Commit**

  ```bash
  git add apps/web/src/App.tsx
  git commit -m "feat: remove GameModeTipModal auto-show — mode info now in HelpModal"
  ```

---

## Task 6: TypeScript check and final test run

- [ ] **Step 1: TypeScript check**

  ```bash
  cd apps/web && npx tsc -b --noEmit
  ```

  Expected: no errors.

- [ ] **Step 2: Full test suite**

  ```bash
  cd apps/web && npm test
  ```

  Expected: all tests PASS.

- [ ] **Step 3: Build check**

  ```bash
  cd apps/web && npm run build
  ```

  Expected: build succeeds, no errors.
