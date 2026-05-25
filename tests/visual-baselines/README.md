# Visual baselines — Phase 2 INF-04

60 frozen PNG screenshots of realufo.org — 15 archives × 4 viewports —
captured from the live GitHub Pages production origin on Phase 2 entry.
These are the pixel contract the Phase 3+ SSG output must honor.

## Purpose

The CI gate in `.github/workflows/quality-gates.yml` (Plan 02-08) runs
`tests/visual-regression.spec.ts` against the CF Pages preview URL on every
PR. Playwright compares each rendered page against the matching baseline
PNG below; a > 0.1 % pixel diff hard-fails the PR (D-16 — see
`.planning/phases/02-infrastructure-ci-scaffolding/02-CONTEXT.md`).

## D-17 invariant — NEVER auto-regen

Re-running `scripts/capture-baselines.py` **overwrites** these PNGs. That
is intentional, but ONLY for operator-initiated visual-change
acknowledgments. The rules:

- **CI workflows MUST NEVER invoke `scripts/capture-baselines.py`.** The
  capture script is operator-only, by design. Grep verification:
  `grep -r 'capture-baselines' .github/workflows/` must return empty
  forever.
- **PR reviewers MUST NEVER suggest "just regen the baseline"** without
  the operator first approving the underlying visual change.
- **A baseline change requires a separate, dedicated commit** with a
  rationale linking to the source-of-truth change (CLAUDE.md §3.1 update,
  a Phase 4 PR that intentionally reshaped the markup, etc.).

### Explicit recapture procedure

When an intentional visual change ships (Phase 4 SSG migration introduces
new markup, CLAUDE.md §3.1 tone-colour update, etc.):

1. **Operator deletes the affected PNGs:**
   ```bash
   rm tests/visual-baselines/<archive>-<viewport>.png
   # or for a global change:
   rm tests/visual-baselines/*-360.png
   ```
2. **Operator runs the capture script:**
   ```bash
   python3 scripts/capture-baselines.py --archive <slug>
   # or --viewport 360 for global
   # or no flags for full 60-PNG recapture
   ```
   See "Runtime setup" below for the venv requirement.
3. **Operator inspects the new PNG visually before staging.** Open the
   file; confirm the change matches the source-of-truth diff.
4. **Operator commits with explicit rationale:**
   ```bash
   git add tests/visual-baselines/<archive>-<viewport>.png
   git commit -m "test(visual): intentional baseline recapture for <archive> — <reason>"
   ```
5. **PR description must reference the source-of-truth change.**
   Examples: "CLAUDE.md §3.1 tone-colour update for Brazil (commit abc1234)",
   "Phase 4 PR #42 reshaped the hero-carousel markup".

## Capture source

**D-12: live <https://realufo.org> production GitHub Pages origin.** Not
the CF Pages preview, not local dev server, not Wayback. Rationale:
pixel-true to what real users see today; CSS fonts that the browser
fetches from Google Fonts at runtime must render identically to what the
final SSG output produces.

## File naming

`<archive_slug>-<viewport_width>.png`

15 archives (per CLAUDE.md §2) × 4 widths (D-14: 360 / 768 / 1024 / 1440)
= **60 files** (D-13).

| Archive slug | Path on realufo.org |
| --- | --- |
| `wargov` | `/` (root — historical: war.gov / PURSUE predates the others) |
| `aaro` | `/aaro/` |
| `nasa` | `/nasa/` |
| `nara` | `/nara/` |
| `geipan` | `/geipan/` |
| `uk` | `/uk/` |
| `brazil` | `/brazil/` |
| `chile` | `/chile/` |
| `argentina` | `/argentina/` |
| `canada` | `/canada/` |
| `italy` | `/italy/` |
| `nz` | `/nz/` |
| `peru` | `/peru/` |
| `spain` | `/spain/` |
| `uruguay` | `/uruguay/` |

## Size budget

D-13: raw PNG, **not LFS**, ~50-200 KB each, ~6 MB total for all 60.

If any single PNG exceeds 500 KB, the operator should re-capture without
`--full-page` — only above-the-fold capture is required for INF-04. The
default mode is above-the-fold; `--full-page` is opt-in.

## Runtime setup

The capture script depends on the Python `playwright` bindings, which are
**not** a project dev-dep (the project's Playwright is the TypeScript test
runner, installed via `pnpm`). The capture script is operator-run on
demand, so the operator sets up a venv once:

```bash
# Python 3.11 venv recommended — Python 3.14 has wheel-build issues with
# greenlet (Playwright's eventloop dep) on some platforms.
python3.11 -m venv .venv
source .venv/bin/activate
pip install playwright==1.49.0
playwright install chromium
```

Then:

```bash
source .venv/bin/activate
python3 scripts/capture-baselines.py            # capture all 60
python3 scripts/capture-baselines.py --check    # verify all 60 present
```

`--check` does NOT need the venv (no `playwright` import on that code path).

## Verification

After any recapture, run:

```bash
python3 scripts/capture-baselines.py --check
# must print "60 / 60 baselines present" and exit 0

find tests/visual-baselines -name '*.png' -size +1M
# must return empty (no full-page misfires)
```
