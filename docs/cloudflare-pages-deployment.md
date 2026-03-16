# Cloudflare Pages Deployment

The app deploys to Cloudflare Pages via GitHub Actions (manual trigger).

---

## Step 1 — Create a Cloudflare account

Sign up free at **cloudflare.com** (no credit card needed).

---

## Step 2 — Create a Pages project

1. Cloudflare dashboard → **Workers & Pages**
2. Click **Create application**
3. Click **Get started**
4. Select **Drag and drop your files**
5. Enter project name: **`ipl-games`** (must match `projectName` in the workflow)
6. Drag any dummy file (e.g. an empty `index.html`) into the upload area
7. Click **Deploy site**

Your project will be accessible at `ipl-games.pages.dev`. The GitHub Actions workflow
will overwrite it on the first real deploy.

---

## Step 3 — Get your credentials

**Account ID:**
Cloudflare dashboard → right sidebar → **Account ID**

**API Token:**
1. Dashboard → avatar (top right) → **My Profile → API Tokens**
2. Click **Create Token → Create Custom Token**
3. Name it (e.g. `ipl-games-deploy`)
4. Under **Permissions** add: `Account` / `Cloudflare Pages` / **Edit**
5. Click **Continue to summary → Create Token**
6. Copy the token immediately — it won't be shown again

---

## Step 4 — Add secrets to GitHub

Repo → **Settings → Secrets and variables → Actions → New repository secret**:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

(`GITHUB_TOKEN` is automatic — no action needed.)

---

## Step 5 — Point your domain

1. Cloudflare dashboard → your Pages project → **Custom Domains → Add domain**
2. Enter `cluster4.games`
3. Cloudflare will prompt you to update GoDaddy nameservers to point to Cloudflare — follow those instructions

---

## Step 6 — Deploy

GitHub → **Actions → Deploy to Cloudflare Pages → Run workflow**

---

## Workflow file

`.github/workflows/deploy-cloudflare.yml` — triggers on `workflow_dispatch` only.

Builds the Vite app with `VITE_BASE_URL=/` and uploads `apps/web/dist/` to the
`ipl-games` Cloudflare Pages project via the `cloudflare/pages-action@v1` action.

---

## All deployment workflows

| Workflow | File | Trigger | Target |
|----------|------|---------|--------|
| Deploy to GitHub Pages | `deploy-gh-pages.yml` | Push to `main` + manual | GitHub Pages (subpath URL) |
| Deploy to GoDaddy | `deploy-godaddy.yml` | Manual only | GoDaddy shared hosting via FTP |
| Deploy to Cloudflare Pages | `deploy-cloudflare.yml` | Manual only | Cloudflare Pages (custom domain) |
