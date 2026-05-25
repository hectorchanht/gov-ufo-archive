# Testing Patterns

**Analysis Date:** 2026-05-25

## Test Framework

**Runner:** None. This is a static-HTML archive — there are no unit tests, no integration tests, no E2E tests, no Jest / Vitest / pytest / shellcheck harness in this repo.

A repo-wide search confirms it:

```bash
find . -name "*.test.*" -o -name "*.spec.*" -o -name "test_*.py" -o -name "*_test.py"
# → no results

ls /Users/laichan/code/war-gov-ufo-release/tests 2>/dev/null
# → directory does not exist
```

No `package.json`, no `requirements.txt`, no `pyproject.toml`, no `pytest.ini`. The closest thing to a dependency manifest is `pip install curl_cffi` inside `.github/workflows/scrape.yml:25` (single transitive dependency for one scraper).

**What this project uses instead:** CI gates on **lint / link-check / accessibility / SEO scores**, plus a manifest-shape validator, plus heavy reliance on manual mobile testing at 360 px.

**Assertion library:** Not applicable.

**Run commands:** Not applicable. The CI workflows below are the closest equivalent to a test suite — they all also run via `workflow_dispatch` so a maintainer can trigger them manually from the Actions tab.

## Test File Organization

Not applicable — no test files exist. Quality gating happens via four GitHub Actions workflows under `.github/workflows/` plus one in-repo validator:

| File | Role | When it runs |
|------|------|--------------|
| `.github/workflows/html-validate.yml` | html-validate against every committed `.html` | push to main + PRs touching HTML + manual |
| `.github/workflows/lighthouse.yml` | Lighthouse CI against 8 representative URLs | push to main + PRs touching HTML/CSS/JS + manual |
| `.github/workflows/links.yml` | lychee broken-link sweep over every `.html` | push to main + PRs touching HTML + Mondays 07:00 UTC + manual |
| `.github/workflows/scrape.yml` | Weekly scrape-rebuild-commit cycle | Mondays 06:00 UTC + manual |
| `.github/workflows/sync-nav.yml` | Drift gate — verify nav is up to date | (see workflow) |
| `.github/workflows/sync-footer.yml` | Drift gate — verify footer is up to date | (see workflow) |
| `scripts/validate-manifests.py` | JSON manifest schema validation | manual (not yet wired into CI) |

## Test Structure

Not applicable. The "tests" are CI workflow steps. The shape of each gate:

**HTML validation** (`.github/workflows/html-validate.yml`):
```bash
find . -name "*.html" \
  -not -path "./node_modules/*" \
  -not -path "*/.cache/*" \
  -not -path "./aaro/pages/*" \
  -not -path "./nara/pages/*" \
  -not -path "./.lighthouseci/*" \
  -print0 \
  | xargs -0 npx html-validate --config .htmlvalidate.json --formatter stylish
```
Rules in `.htmlvalidate.json` — `html-validate:recommended` minus a long list of rules disabled because inline styles and inline event handlers are intentional choices (CLAUDE.md §3). Scraped upstream HTML in `aaro/pages/` and `nara/pages/` is excluded — it ships malformed asp.net markup.

**Lighthouse CI** (`.github/workflows/lighthouse.yml`):
- Spins up `python3 -m http.server 8000` against the repo, waits up to 30 s for it to come up via `curl -fs http://localhost:8000/`, runs `npx lhci autorun --config=.lighthouserc.json`.
- Audits 8 URLs: `/`, `/search.html`, `/timeline.html`, `/map.html`, `/about.html`, `/aaro/`, `/aaro/tic-tac.html`, `/uk/rendlesham.html` (`.lighthouserc.json:4-13`).
- Hard gates: **accessibility ≥ 0.90** (error), **SEO ≥ 0.90** (error). Warning gates: performance ≥ 0.80, best-practices ≥ 0.85.
- Uploads results to `temporary-public-storage` for inspection.

**Link-check** (`.github/workflows/links.yml`):
- Uses `lycheeverse/lychee-action@v2` with a 7-day cache.
- `--include-fragments` validates `#anchor` targets actually exist in the target page.
- `--accept 200,206,301,302,308,403,429` — treats common Akamai/anti-bot responses (403, 429) as alive.
- `--exclude '^mailto:'` skips mailto.
- `--root-dir ${{ github.workspace }}` resolves root-relative hrefs against the checkout.
- Ignores in `.lycheeignore` (1 449 bytes) cover known-flaky upstream `.mil` / `.gov` hosts.
- **Runs every Monday 07:00 UTC** on a schedule to catch upstream link rot, not just on PRs.

**Manifest validation** (`scripts/validate-manifests.py`):
- Extracts the inline `<script id="arch-data">` (or `<script id="archive-manifest">`) JSON block from every archive.
- Validates each record has a title, at least one of `url`/`src`/`local`, parseable URLs, no `javascript:` / `data:` schemes.
- Allows unknown fields (warning only) — archives evolve.
- Exits 0 on success, 1 on errors, 1 on warnings if `--strict`.
- Currently invoked **manually**, not in any workflow file. Wiring it into CI would be a small follow-up.

## Mocking

Not applicable. Nothing to mock — there's no test harness. The only fakery is:

- **Realistic Chrome UA string** in `scripts/dl-*.sh` to bypass Akamai's "default curl UA" blocks:
  ```bash
  UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
  ```
- **Wayback Machine fallback** in `scripts/dl-aaro.sh:53-82` when direct fetch is blocked. Not a mock — a real second source.

## Fixtures and Factories

Not applicable. The closest equivalents are the **cached upstream snapshots** the scrape pipeline produces:

| Cache file | Purpose | Producer |
|-----------|---------|----------|
| `aaro/.cache/parsed.json` | Parsed aaro.mil page bodies | `scripts/parse-aaro.py` |
| `aaro/.cache/evidence.json` | Extracted PDF/video/image manifest | `scripts/extract-evidence.py` |
| `aaro/.cache/vid-todo.txt` | Per-run video work-queue | `scripts/dl-aaro.sh:128` |
| `aaro/.cache/pdf-todo.txt` | Per-run PDF work-queue | `scripts/dl-aaro.sh:158` |
| `aaro/.cache/img-todo.txt` | Per-run image work-queue | `scripts/dl-aaro.sh:186` |
| `scripts/dvids2dod-r01.json` | DVIDS ID → DOD record-ID map (Release 01) | `scripts/resolve-dvids-r01.py` |
| `scripts/dvids2dod-r02.json` | DVIDS ID → DOD record-ID map (Release 02) | one-off DVIDS API resolve |
| `release-manifest.json` | Per-release tag → file list (~ 54 KB) | `scripts/backfill-release.py` |

These are gitignored where they're large (`.cache/`), tracked where they're small reference data (`dvids2dod-*.json`, `release-manifest.json`).

**Location of "fixtures":** `<archive>/.cache/` per archive; `scripts/` for cross-archive maps.

## Coverage

Not applicable. **There are no code-coverage requirements** because there are no tests.

The coverage analogue this project actually cares about is **asset-coverage**, reported at the end of every build script:
```python
print(f'  total assets: {stats["total"]}, local: {stats["local_total"]}')
print(f'  videos local: {stats["videos_local"]}/{stats["videos_total"]}')
print(f'  pdfs local: {stats["pdfs_local"]}/{stats["pdfs_total"]}')
print(f'  imgs local: {stats["imgs_local"]}/{stats["imgs_total"]}')
```
(`scripts/build-aaro.py:1357-1360`, `scripts/build-nasa.py:747-748`). The summary block at the bottom of `scripts/sync.sh:225-247` aggregates the same numbers across all archives.

**View coverage:** Run `./scripts/sync.sh --no-build` and watch the "Local-asset summary" stanza print, or run any individual `scripts/build-*.py` and read its tail.

## Test Types

**Unit Tests:** None.

**Integration Tests:** None.

**E2E Tests:** None. There is no Playwright, Cypress, or WebDriver harness.

**The CI gates substitute for these in practice:**

| Gate | What it actually catches |
|------|--------------------------|
| html-validate | Malformed HTML, missing required attributes, deprecated elements |
| Lighthouse accessibility ≥ 0.90 | Missing alt text, contrast failures, focus traps, missing landmark roles, button sizing |
| Lighthouse SEO ≥ 0.90 | Missing meta description, missing canonical, invalid robots, missing structured data |
| Lighthouse performance warn-only | Bundle bloat, unused CSS, LCP > 2.5 s |
| lychee | Broken internal links, broken anchor fragments, dead upstream `.mil` / `.gov` URLs |
| `scripts/validate-manifests.py` | Manifest records missing a title or any action target |

## Ad-Hoc Verification Methods

These are the **real** ways issues get caught in this project. Document them honestly because new contributors need to know what to actually do.

**1. Local serve and click around:**
```bash
cd /Users/laichan/code/war-gov-ufo-release
python3 -m http.server 8000
# Open http://localhost:8000/ and walk every archive, every story page,
# every action button. This is how 90% of bugs are found.
```
The Lighthouse CI workflow does exactly the same — `python3 -m http.server 8000` then audit — so what passes locally passes in CI.

**2. Mobile-first manual testing (CLAUDE.md §8):**
- Open Chrome / Safari DevTools, **set viewport to 360 px first**, then scale up.
- Walk: hamburger toggle → carousel arrows + dots → archive tabs (must wrap, never horizontal-scroll) → filter dropdowns → search input → first card → lightbox open / prev / next / close → swipe gestures (use DevTools touch emulator) → footer.
- Confirm no element exceeds 100vw (no horizontal scroll).
- Confirm every tap target is ≥ 44 × 44 px effective.

**3. Sync + rebuild dry run:**
```bash
./scripts/sync.sh --no-build    # downloads only, skip HTML regen
./scripts/sync.sh --all         # full re-sync + regen everything
./scripts/sync.sh --<slug>-only # one archive in isolation
```
Idempotent — safe to re-run. The "Local-asset summary" stanza at the end is the integration-test report.

**4. Manifest validation (manual):**
```bash
python3 scripts/validate-manifests.py
python3 scripts/validate-manifests.py --strict   # treat warnings as errors
python3 scripts/validate-manifests.py aaro nasa  # subset
```

**5. CI workflow dry run via workflow_dispatch:**
Every workflow has `workflow_dispatch:` — trigger from the Actions tab to test changes without pushing.

**6. PR sanity checklist (informal, observed across recent commits):**
- Does the new archive's `<script id="arch-data">` parse as valid JSON?
- Does every Download button route to a URL that doesn't 404 (release URL, not bare local path that may be missing)?
- Does Source ↗ point at the official upstream, not at `realufo.org`?
- Does the hero carousel autoplay and pause on hover?
- Does Esc / arrow keys / swipe work in the lightbox?
- Has the `?q=` URL state on `/search.html` been preserved on reload?

## Common Patterns

**"Test" via `--check` mode on build helpers:**

The drift-detection workflows (`.github/workflows/sync-nav.yml`, `.github/workflows/sync-footer.yml`) run their associated scripts in a `--check` mode that compares generated output against committed HTML and exits non-zero on drift. See `scripts/sync-nav.py` and `scripts/sync-footer.py`.

```python
# Pattern: sync-nav.py walks every HTML file, builds the canonical <nav> via
# make_nav(), and either rewrites the file (default) or exits 1 if the file's
# current nav differs from the generated one (--check mode).
```

This is the closest pattern to a unit test in the codebase — it's a **shape-equality check** that runs in CI.

**Async / network testing:** Not applicable. The download scripts handle network failure by:
1. Returning non-zero from `fetch` / `fetch_url`
2. Logging `[FAIL]` to stdout
3. Removing the partial file
4. Letting the caller's loop continue (no `set -e`)

Failures show up in the per-run log and in the final `--no-videos` style summary, never as an exception trace.

## What to Add If This Project Ever Grows a Test Suite

The natural seams for first tests:

1. **`scripts/validate-manifests.py`** — wire into CI (`.github/workflows/manifests.yml`). It already returns 0/1 cleanly.
2. **Python unit tests for `scripts/templates/nav.py`** — `make_nav()` is pure, has well-defined inputs (`PINNED`, `SITE_PAGES`, `MORE`, `STORIES`, `current_slug`, `depth`). Snapshot-test its output.
3. **Playwright smoke tests** against `python3 -m http.server 8000` — same setup Lighthouse already uses. Best ROI: lightbox open/close/nav/swipe on one IMG, one VID, one PDF (local), one PDF (release URL); search restore from `?q=`; mobile hamburger toggle at 360 px viewport.
4. **Shellcheck** on every `scripts/dl-*.sh` — would flag the legitimately-quirky `set -uo pipefail` (no `-e`) but also catches real bugs.

None of these exist today. Don't claim coverage that isn't there.

---

*Testing analysis: 2026-05-25*
