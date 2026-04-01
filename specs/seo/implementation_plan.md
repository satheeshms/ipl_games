# SEO Optimisation — Implementation Plan

**Spec Version:** 1.0
**Date:** 2026-04-01
**Status:** Draft
**References:** `specs/seo/requirements.md`

---

## 1. Overview

This plan delivers SEO for Cluster 4 - IPL Edition in four self-contained phases. Each phase is independently deployable and leaves the app in a shippable state. No architecture overhaul is required; the SPA remains client-rendered throughout.

**Key constraints:**
- `vite.config.ts` reads `process.env.VITE_BASE_URL` for Vite's `base` option.
- Only the Cloudflare Pages workflow is active; GitHub Pages and GoDaddy deployments are deprecated and removed from scope.
- Puzzle JSONs live at `apps/web/public/puzzles/ipl/YYYY-MM-DD.json`.
- The app has no routing; a single root URL is the canonical address for all puzzle dates.
- Game background colour: `#0d1a0e`; brand accent: `#F5A623`; favicon red: `#C41E3A`.

---

## 2. Phase 1 — Static HTML Head

**Goal:** Establish all static meta tags in `index.html` and add `robots.txt`. No new npm dependencies.

### 2.1 Update `apps/web/index.html`

Replace the current minimal `<head>` with the full set of static tags. Order within `<head>`: charset → viewport → title → canonical → SEO meta → OG meta → Twitter meta → mobile/PWA meta → favicon → apple-touch-icon → JSON-LD.

Tags to add:

```html
<!-- SEO -->
<meta name="description"
      content="Cluster 4 – IPL Edition: the daily cricket word puzzle. Find 4 groups of 4 IPL-themed items. One puzzle per day, free to play." />
<meta name="keywords"
      content="IPL puzzle, cricket word game, IPL Cluster 4, daily puzzle, cricket quiz, IPL trivia, Cluster4" />
<meta name="author"  content="Cluster4" />
<meta name="robots"  content="index, follow" />
<link rel="canonical" href="%VITE_CANONICAL_URL%" />

<!-- Open Graph -->
<meta property="og:type"         content="website" />
<meta property="og:site_name"    content="Cluster4" />
<meta property="og:title"        content="Cluster 4 - IPL Edition" />
<meta property="og:description"  content="The daily IPL cricket word puzzle. Find 4 hidden groups of 4 items. Free, no login." />
<meta property="og:url"          content="%VITE_CANONICAL_URL%" />
<meta property="og:image"        content="%VITE_CANONICAL_URL%/og-image.png" />
<meta property="og:image:width"  content="1200" />
<meta property="og:image:height" content="630" />

<!-- Twitter Card -->
<meta name="twitter:card"        content="summary_large_image" />
<meta name="twitter:title"       content="Cluster 4 - IPL Edition" />
<meta name="twitter:description" content="The daily IPL cricket word puzzle. Find 4 hidden groups of 4 items. Free, no login." />
<meta name="twitter:image"       content="%VITE_CANONICAL_URL%/og-image.png" />

<!-- Mobile / PWA -->
<meta name="theme-color"                           content="#0d1a0e" />
<meta name="mobile-web-app-capable"                content="yes" />
<meta name="apple-mobile-web-app-capable"          content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="apple-mobile-web-app-title"            content="IPL Cluster 4" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
```

**Note on `%VITE_CANONICAL_URL%` substitution:** Vite replaces `%VITE_*%` tokens in `index.html` at build time. Verify this works for `<link>` and `<meta>` attribute values in Vite 8 before finalising. If it does not, add a minimal inline `transformIndexHtml` plugin in `vite.config.ts` to perform string replacement — no additional npm package is needed for this.

### 2.2 Static JSON-LD in `index.html`

Add two static JSON-LD blocks inside `<head>`:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Cluster4",
  "url": "%VITE_CANONICAL_URL%"
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Cluster 4 - IPL Edition",
  "url": "%VITE_CANONICAL_URL%",
  "applicationCategory": "GameApplication",
  "operatingSystem": "Any",
  "browserRequirements": "Requires JavaScript",
  "inLanguage": "en",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  }
}
</script>
```

### 2.3 Create `apps/web/public/robots.txt`

Commit a static placeholder for local development. Phase 3 overwrites this at build time using `VITE_CANONICAL_URL`.

```
User-agent: *
Disallow:

Sitemap: https://cluster4.games/sitemap.xml
```

### 2.4 Create the OG image asset

Produce `apps/web/public/og-image.png` (1200×630 px, ≤ 200 KB). Suggested content:
- Background: `#0d1a0e` (dark green)
- Game title "Cluster 4 - IPL Edition" in large white text
- Four coloured squares (yellow / green / blue / purple) representing the category colours
- Tagline "Daily IPL cricket puzzle" in smaller text
- Brand accent `#F5A623` for decorative elements
- Cricket-ball motif (can reuse `favicon.svg` artwork)

### 2.5 Create the Apple touch icon

Produce `apps/web/public/apple-touch-icon.png` (180×180 px). Use the cricket-ball motif from `favicon.svg` with `#C41E3A` background, enlarged to Apple's safe-zone specifications.

### 2.6 Update the Cloudflare Pages CI/CD workflow to pass `VITE_CANONICAL_URL`

Edit the `Build` step `env` block in `.github/workflows/deploy-cloudflare.yml`:

```yaml
env:
  VITE_BASE_URL: /
  VITE_CANONICAL_URL: https://cluster4.games
```

### Phase 1 Checklist

- [ ] `index.html` updated with all static meta tags in correct order.
- [ ] `%VITE_CANONICAL_URL%` substitution verified locally (`VITE_CANONICAL_URL=http://localhost:4173 npm run build`).
- [ ] Both static JSON-LD blocks present in built `index.html`.
- [ ] `public/robots.txt` created.
- [ ] `public/og-image.png` created and committed (≤ 200 KB, 1200×630 px).
- [ ] `public/apple-touch-icon.png` created and committed (180×180 px).
- [ ] `deploy-cloudflare.yml` updated with `VITE_CANONICAL_URL`.
- [ ] `apps/web/README.md` documents both env vars.
- [ ] Lighthouse SEO score ≥ 90 on `vite preview` build.

---

## 3. Phase 2 — Dynamic Head Management

**Goal:** Install `react-helmet-async` and create a `<GameSEO>` component that updates title and OG tags per puzzle once it loads.

### 3.1 Install `react-helmet-async`

```bash
# from apps/web/
npm install react-helmet-async
```

This is the only new production runtime dependency in this entire SEO initiative. Verify React 19 compatibility before installing; if incompatible, evaluate `@unhead/react` as a drop-in alternative.

### 3.2 Update `apps/web/src/main.tsx`

Wrap `<App>` in `<HelmetProvider>`:

```tsx
import { HelmetProvider } from 'react-helmet-async';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <HelmetProvider>
      <App />
    </HelmetProvider>
  </StrictMode>,
);
```

### 3.3 Create `apps/web/src/components/GameSEO.tsx`

A purely presentational component — receives `Puzzle`, emits `<Helmet>` tags only. No data fetching, no visible DOM output.

Props:
```ts
interface GameSEOProps {
  puzzle: Puzzle;
}
```

Tags produced:
- `<title>`: `Puzzle #{{edition}} – {{date}} | Cluster 4 - IPL Edition`
- `<meta name="description">`: `"Today's IPL Cluster 4 puzzle (#{{edition}}) — find 4 groups across {{n}} categories. {{date}}."`
- `<link rel="canonical">`: `import.meta.env.VITE_CANONICAL_URL`
- `<meta property="og:title">`: same as title (without the ` | Cluster 4 - IPL Edition` suffix)
- `<meta property="og:description">`: same as description
- `<meta property="og:url">`: `import.meta.env.VITE_CANONICAL_URL`
- Dynamic `Game` JSON-LD (see §3.4)

### 3.4 Dynamic `Game` JSON-LD inside `<GameSEO>`

Serialise with `JSON.stringify` (not a template literal) to avoid XSS from any special characters in puzzle data:

```json
{
  "@context": "https://schema.org",
  "@type": "Game",
  "name": "Cluster 4 - IPL Edition",
  "description": "A daily IPL cricket word puzzle. Find 4 hidden groups of 4 items.",
  "url": "{{VITE_CANONICAL_URL}}",
  "datePublished": "{{puzzle.date}}",
  "identifier": "{{puzzle.edition}}",
  "inLanguage": "en",
  "numberOfPlayers": {
    "@type": "QuantitativeValue",
    "minValue": 1,
    "maxValue": 1
  },
  "gamePlayMode": "SinglePlayer"
}
```

Only `puzzle.date`, `puzzle.edition`, and `puzzle.categories.length` may appear in JSON-LD. Answer hashes and category items must not be included.

### 3.5 Update `apps/web/src/App.tsx`

Render `<GameSEO>` conditionally after a successful puzzle load:

```tsx
{puzzle && <GameSEO puzzle={puzzle} />}
```

Placement at the top of the JSX tree is conventional; the component renders no visible DOM.

### 3.6 Update `apps/web/src/vite-env.d.ts`

```ts
interface ImportMetaEnv {
  readonly VITE_BASE_URL: string;
  readonly VITE_CANONICAL_URL: string;
}
```

### Phase 2 Checklist

- [ ] `react-helmet-async` installed; React 19 compatibility confirmed.
- [ ] `HelmetProvider` wraps `App` in `main.tsx`.
- [ ] `GameSEO.tsx` created with all required tags and JSON-LD.
- [ ] `App.tsx` renders `<GameSEO puzzle={puzzle} />` when puzzle is loaded.
- [ ] `vite-env.d.ts` declares `VITE_CANONICAL_URL`.
- [ ] Manual test: `<title>` updates after puzzle loads; falls back to static value while loading.
- [ ] No existing Vitest tests broken.

---

## 4. Phase 3 — Sitemap Generation

**Goal:** Auto-generate `sitemap.xml` and an environment-aware `robots.txt` before every build.

### 4.1 Create `apps/web/scripts/generate-sitemap.mjs`

Uses only Node.js built-in modules (`fs`, `path`, `url`).

Logic:
1. Read `VITE_CANONICAL_URL` from `process.env`. If unset, print an error and `process.exit(1)`.
2. Enumerate `public/puzzles/ipl/*.json` with `fs.readdirSync`.
3. Extract and validate date strings (`YYYY-MM-DD` regex); skip non-conforming filenames.
4. Sort dates ascending.
5. Write `public/sitemap.xml` — one `<url>` per date. All `<loc>` values point to the canonical root (SPA; no per-puzzle URLs). `<lastmod>` = puzzle date, `<changefreq>` = `yearly`, `<priority>` = `0.8` for today's UTC date, `0.5` for all others.
6. Write `public/robots.txt`:
   ```
   User-agent: *
   Disallow:

   Sitemap: {{VITE_CANONICAL_URL}}/sitemap.xml
   ```
7. Print: `Generated sitemap.xml with N entries. robots.txt updated.`

### 4.2 Update `apps/web/package.json`

Add a `prebuild` hook so the script runs automatically before every `npm run build`:

```json
"scripts": {
  "prebuild": "node scripts/generate-sitemap.mjs",
  "build": "tsc -b && vite build",
  ...
}
```

The `dev` script does not trigger `prebuild` — intentional, as developers do not need the sitemap locally.

### 4.3 Add generated files to `.gitignore`

Since `sitemap.xml` and `robots.txt` are generated at build time, they should not be committed:

```
# Add to root .gitignore or apps/web/.gitignore
apps/web/public/sitemap.xml
apps/web/public/robots.txt
```

Note: Vite copies everything from `public/` to `dist/` at build time, so generated files will be included in the deploy artefact regardless of `.gitignore`.

### Phase 3 Checklist

- [ ] `scripts/generate-sitemap.mjs` created and tested locally.
- [ ] Script exits with code 1 if `VITE_CANONICAL_URL` is unset.
- [ ] Output `sitemap.xml` validates against the sitemap XSD.
- [ ] `package.json` `prebuild` hook added.
- [ ] `npm run build` locally produces `dist/sitemap.xml` and `dist/robots.txt` with correct canonical URLs.
- [ ] `sitemap.xml` and `robots.txt` added to `.gitignore`.
- [ ] Cloudflare Pages CI/CD pipeline passes; `Sitemap:` URL in `robots.txt` is correct.
- [ ] `apps/web/README.md` documents the `prebuild` behaviour.

---

## 5. Phase 4 — Structured Data Hardening and Tests

**Goal:** Validate all JSON-LD for schema.org compliance, add an SEO smoke test, and document the architecture.

### 5.1 Validate and fix `Game` JSON-LD

Run the Phase 2 `Game` JSON-LD through Google's Rich Results Test. Common adjustments:
- If `"identifier"` plain string is rejected, use `PropertyValue`:
  ```json
  "identifier": { "@type": "PropertyValue", "name": "edition", "value": "{{edition}}" }
  ```
- Confirm `"numberOfPlayers"` with `QuantitativeValue` is accepted.
- Ensure `"inLanguage": "en"` is present on both `Game` and `WebApplication` blocks.

### 5.2 Audit JSON-LD for data leakage

Confirm that `puzzle.categories[n].hash`, category titles, and item names do not appear in any JSON-LD output. Only `puzzle.date`, `puzzle.edition`, and `puzzle.categories.length` are permitted.

### 5.3 Add SEO smoke test

Create `apps/web/src/test/seo.test.tsx`. Using React Testing Library with a mock `Puzzle` object, render:

```tsx
<HelmetProvider>
  <GameSEO puzzle={mockPuzzle} />
</HelmetProvider>
```

Assert:
- `document.title` matches `Puzzle #{{edition}} – {{date}} | Cluster 4 - IPL Edition`.
- A `<link rel="canonical">` element exists in the document head.
- The `og:title` meta tag reflects the puzzle edition and date.

### 5.4 Document SEO architecture in `apps/web/README.md`

Add a "SEO" section covering:
- Which tags are static (`index.html`) vs. dynamic (`<GameSEO>`).
- How `VITE_CANONICAL_URL` is used and where to set it per deployment target.
- How to regenerate the sitemap locally.
- How to produce/update the OG image if branding changes.

### Phase 4 Checklist

- [ ] `Game` JSON-LD validated — zero errors in Google Rich Results Test.
- [ ] `Organization` and `WebApplication` JSON-LD validated — zero errors.
- [ ] Audit confirms no answer data in JSON-LD.
- [ ] `seo.test.tsx` written and passing.
- [ ] `apps/web/README.md` SEO section complete.
- [ ] Lighthouse audit on production build: SEO ≥ 90, Performance unaffected, no new console errors.

---

## 6. Phase Dependencies

```
Phase 1 (static HTML + robots.txt)
    └── Phase 2 (react-helmet-async dynamic tags)
            └── Phase 4 (structured data hardening, tests)
Phase 3 (sitemap generator)  ← independent; can run in parallel with Phase 2
                               depends only on Phase 1 CI/CD env var additions
```

---

## 7. File Inventory

| File | Action | Phase |
|------|--------|-------|
| `apps/web/index.html` | Update — add all static meta tags and JSON-LD | 1 |
| `apps/web/public/robots.txt` | Create (placeholder; overwritten by generator) | 1 |
| `apps/web/public/og-image.png` | Create — 1200×630 px brand image | 1 |
| `apps/web/public/apple-touch-icon.png` | Create — 180×180 px | 1 |
| `.github/workflows/deploy-cloudflare.yml` | Update — add `VITE_CANONICAL_URL` | 1 |
| `apps/web/README.md` | Update — document env vars | 1 |
| `apps/web/src/main.tsx` | Update — wrap in `HelmetProvider` | 2 |
| `apps/web/src/components/GameSEO.tsx` | Create — dynamic head component | 2 |
| `apps/web/src/App.tsx` | Update — render `<GameSEO>` | 2 |
| `apps/web/src/vite-env.d.ts` | Update — declare `VITE_CANONICAL_URL` | 2 |
| `apps/web/scripts/generate-sitemap.mjs` | Create — sitemap + robots.txt generator | 3 |
| `apps/web/package.json` | Update — add `prebuild` script | 3 |
| `.gitignore` | Update — ignore generated sitemap and robots.txt | 3 |
| `apps/web/src/test/seo.test.tsx` | Create — smoke test for `<GameSEO>` | 4 |

---

## 8. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Vite 8 `%VITE_*%` substitution may not work inside `<meta>` attribute values or JSON-LD `<script>` blocks | Medium | Test locally in Phase 1 first. If needed, add a minimal inline `transformIndexHtml` plugin in `vite.config.ts` — no additional package required. |
| `react-helmet-async` may have React 19 compatibility issues | Low-Medium | Check release notes before installing. If incompatible, use `@unhead/react` as a drop-in alternative. |
| Crawlers that do not execute JavaScript miss dynamic `<GameSEO>` tags | Accepted | Googlebot renders JavaScript. Static fallback tags in `index.html` provide sufficient coverage for other crawlers. Full SSR/SSG is out of scope. |
| `prebuild` hook fails silently if `VITE_CANONICAL_URL` is unset in a local build | Addressed | Generator script calls `process.exit(1)` with a clear error message — build fails visibly. |
