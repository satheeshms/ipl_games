# SEO Optimisation — Requirements

**Spec Version:** 1.0
**Date:** 2026-04-01
**Status:** Draft
**References:** `specs/connections/requirements.md`, `specs/rebrand/requirements.md`

---

## 1. Overview

Cluster 4 - IPL Edition is a static SPA (React 18 + Vite) with no server-side rendering. SEO must therefore be achieved entirely through static HTML metadata, client-side head management, a generated sitemap, and structured data. The goal is to maximise organic discoverability for cricket fans searching for daily IPL word games, and to produce rich social-share previews when puzzle links are shared.

---

## 2. Goals

- Make the game discoverable by search engines for relevant IPL and word-game queries.
- Produce rich Open Graph and Twitter Card previews when users share the site on social media.
- Establish a single authoritative canonical URL to avoid duplicate-content penalties.
- Provide structured data so search engines can surface the game as a recognised interactive application.
- Ensure all meta tags and sharing infrastructure remain maintainable without adding runtime backend complexity.

---

## 3. Functional Requirements

### 3.1 Discoverability

| ID | Requirement |
|----|-------------|
| DISC-01 | A `robots.txt` file must be served at the root path of every deployment target, permitting all crawlers (`User-agent: *`, `Disallow:` empty) and declaring the sitemap URL. |
| DISC-02 | A `sitemap.xml` file must list one `<url>` entry per published puzzle date, using the canonical base URL (see §3.6) as the prefix. |
| DISC-03 | Each sitemap entry must carry a `<lastmod>` equal to the puzzle date and a `<changefreq>` of `yearly` (puzzle content for a given date is immutable). |
| DISC-04 | The sitemap must be regenerated automatically as part of every CI/CD build, before `vite build` runs, so newly committed puzzle JSON files are always reflected. |
| DISC-05 | The sitemap generator must be a standalone script (`scripts/generate-sitemap.mjs`) requiring no build-time dependencies beyond Node.js built-ins; it reads all `*.json` files under `apps/web/public/puzzles/ipl/` and writes `apps/web/public/sitemap.xml`. |

### 3.2 Basic SEO Meta Tags

| ID | Requirement |
|----|-------------|
| META-01 | `index.html` must include a `<meta name="description">` with a concise, keyword-rich description of the game (≤ 160 characters). |
| META-02 | `index.html` must include a `<meta name="keywords">` listing relevant terms (IPL, cricket puzzle, word game, daily puzzle, cricket quiz, IPL trivia, Cluster4). |
| META-03 | A `<link rel="canonical">` tag must be present, pointing to the canonical base URL supplied via the `VITE_CANONICAL_URL` environment variable at build time. |
| META-04 | The default `<title>` in `index.html` must be "Cluster 4 - IPL Edition". Client-side title updates (see §3.4) override this once the puzzle loads. |
| META-05 | `<meta name="author">` should identify the publisher ("Cluster4"). |
| META-06 | `<meta name="robots">` must be present and set to `index, follow`. |

### 3.3 Open Graph and Twitter Card Tags

| ID | Requirement |
|----|-------------|
| OG-01 | `index.html` must include the full set of Open Graph tags: `og:type` (`website`), `og:site_name` (`Cluster4`), `og:title`, `og:description`, `og:url`, and `og:image`. |
| OG-02 | `og:image` must reference a static 1200×630 px PNG (`/og-image.png`) committed to `apps/web/public/`. The image must show the game name, a sample coloured grid, and the tagline "Daily IPL cricket puzzle". |
| OG-03 | `og:image:width` and `og:image:height` must be declared (1200 and 630 respectively). |
| OG-04 | `index.html` must include Twitter Card tags: `twitter:card` (`summary_large_image`), `twitter:title`, `twitter:description`, `twitter:image`, and `twitter:site` (set to the project's Twitter/X handle, or omitted if none exists). |
| OG-05 | When a puzzle is loaded, the `<GameSEO>` component (§3.4) must update `og:title`, `og:description`, and `og:url` dynamically to reflect the current puzzle date and edition. |

### 3.4 Dynamic Head Management

| ID | Requirement |
|----|-------------|
| DYN-01 | The app must use `react-helmet-async` to manage `<head>` tags at runtime; this is the only new runtime dependency permitted in this phase. |
| DYN-02 | `main.tsx` must wrap `<App>` in a `<HelmetProvider>`. |
| DYN-03 | A `<GameSEO>` component must be rendered inside `<App>` whenever a puzzle is successfully loaded. It must receive the `Puzzle` object as a prop and produce the following dynamic tags: `<title>`, `<meta name="description">`, `<link rel="canonical">`, `<meta property="og:title">`, `<meta property="og:description">`, `<meta property="og:url">`. |
| DYN-04 | The dynamic `<title>` format must be: `Puzzle #{{edition}} – {{YYYY-MM-DD}} \| Cluster 4 - IPL Edition`. |
| DYN-05 | The dynamic `og:description` must describe the puzzle concisely, e.g. "Today's IPL Cluster 4 puzzle (#{{edition}}) — find 4 groups across {{n}} categories. {{YYYY-MM-DD}}." where `n` is `puzzle.categories.length`. |
| DYN-06 | The dynamic `og:url` must be constructed as `{{VITE_CANONICAL_URL}}/` (the canonical URL is always the root for this SPA). |
| DYN-07 | When the puzzle has not yet loaded, the static fallback tags in `index.html` must remain active — `<GameSEO>` must not render empty or partial tags. |

### 3.5 Mobile and PWA Meta Tags

| ID | Requirement |
|----|-------------|
| PWA-01 | `index.html` must include `<meta name="theme-color" content="#0d1a0e">` (matching the game background colour). |
| PWA-02 | `index.html` must reference an Apple touch icon: `<link rel="apple-touch-icon" href="/apple-touch-icon.png">`. The PNG must be 180×180 px and committed to `apps/web/public/`. |
| PWA-03 | `index.html` must include `<meta name="mobile-web-app-capable" content="yes">` and `<meta name="apple-mobile-web-app-capable" content="yes">`. |
| PWA-04 | `index.html` must include `<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">`. |

### 3.6 Canonical URL Strategy

| ID | Requirement |
|----|-------------|
| CAN-01 | The Cloudflare Pages CI/CD build must supply `VITE_CANONICAL_URL=https://cluster4.games` (or the confirmed production domain) as a build environment variable. |
| CAN-02 | `VITE_BASE_URL` (for Vite asset paths) and `VITE_CANONICAL_URL` (for canonical/OG URLs) are separate concerns and must not be conflated. |
| CAN-03 | The sitemap generator script must write `robots.txt` using the `VITE_CANONICAL_URL` value so the `Sitemap:` directive is always correct. |

### 3.7 Schema.org Structured Data

| ID | Requirement |
|----|-------------|
| SD-01 | `index.html` must contain a static `<script type="application/ld+json">` block describing the Organisation (`@type: Organization`). |
| SD-02 | When a puzzle loads, `<GameSEO>` must inject a dynamic `<script type="application/ld+json">` describing the current puzzle using the `Game` schema type. |
| SD-03 | The `Game` JSON-LD must include `datePublished` (the puzzle date string) and `identifier` (the puzzle edition number). |
| SD-04 | JSON-LD must not expose the puzzle answer hash or category items — only public-facing metadata. |
| SD-05 | Both JSON-LD blocks must produce zero errors when validated with Google's Rich Results Test. |

### 3.8 Performance

| ID | Requirement |
|----|-------------|
| PERF-01 | SEO implementation must not introduce any render-blocking resources. |
| PERF-02 | The `og:image` PNG must be ≤ 200 KB. |
| PERF-03 | No additional JavaScript bundles beyond `react-helmet-async` are to be introduced in this SEO work. |
| PERF-04 | The sitemap generator script must complete in under 5 seconds for up to 365 puzzle files. |

---

## 4. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-01 | All SEO changes must be backward-compatible — no existing gameplay, state management, hash logic, or localStorage keys must be altered. |
| NFR-02 | The `<GameSEO>` component must be purely presentational (no side effects beyond head management); it must not fetch data. |
| NFR-03 | Spec documents must be reviewed and approved before any code is written, following the project's SDD pattern. |
| NFR-04 | All new environment variables must be documented in `apps/web/README.md`. |

---

## 5. Out of Scope

- Server-side rendering or static site generation (SSG) — the app remains a client-rendered SPA.
- Per-puzzle unique URLs / routing — the app has no router.
- Google Search Console integration, analytics, or tracking pixels.
- Localisation of meta tags.
- AMP pages.

---

## 6. Acceptance Criteria

- [ ] `robots.txt` served at canonical root with correct `Sitemap:` URL.
- [ ] `sitemap.xml` contains one entry per `*.json` file in `public/puzzles/ipl/`.
- [ ] Facebook Sharing Debugger shows correct OG title, description, and 1200×630 image.
- [ ] Google's Rich Results Test returns no errors for the `Game` JSON-LD.
- [ ] Lighthouse SEO score ≥ 90 on a production build served with `vite preview`.
- [ ] `<title>` updates to `Puzzle #{{n}} – {{date}} | Cluster 4 - IPL Edition` once the puzzle loads.
- [ ] No existing Vitest tests are broken.
