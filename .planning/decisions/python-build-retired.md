# ADR — Python Build Legacy Retired (Phase 4 close)

**Status:** Accepted
**Date:** 2026-05-28
**Decided by:** Plan 04-20 (Phase 4 close)
**Related decisions:** D-09 (Astro page ownership), D-10 (Card.astro ↔ normalize-csv.py LOCKED pair), D-28 (Lighthouse soft-then-hard toggle), Phase 4 SCOPE PIVOT (4 active / 11 dormant)
**Related requirements:** SSG-10 (legacy Python build retirement), PERF-04 (HARD Lighthouse gate at Phase 4 close)

---

## Context

realufo.org started as a plain HTML + Python build pipeline: one
`scripts/build-<slug>.py` per archive that emitted a self-contained
HTML page with inline CSS, inline JS, and an embedded manifest. The
SSG migration (Phase 4) ports the 4 active archives (wargov, aaro,
nasa, nara) into Astro 5 / Cloudflare Pages. Plans 04-15..04-18 each
deleted their per-archive Python builder when its Astro page landed.

Several cross-cutting Python scripts survived Wave 6 because they
either (a) had ongoing consumers in `scrape.yml` (the weekly scrape +
rebuild GH Action — Phase 5 SCRP scope), or (b) policed drift between
HTML files via `--check` mode (sync-nav.py, sync-footer.py,
html-validate.yml). Plan 04-20 audits and finalises retirement.

Operator scope pivot (2026-05-28) reduced v1 to 4 active archives but
kept the 11 dormant in the repo. This means `scripts/copy-legacy-
archives.sh` STAYS — it ships the 11 dormant archives (geipan, uk,
brazil, chile, argentina, canada, italy, peru, spain) + partial-port
sub-pages of nz/uruguay/nasa/nara/aaro into `dist/` during postbuild.

---

## Decision

Retire only the active-surface Python build legacy now:

**Deleted by Plan 04-20:**

| Path | Retire reason |
| ---- | -------------- |
| `scripts/build-wargov.py` | Astro owns `/` via `src/pages/index.astro` (Plan 03-05) |
| `scripts/build-details.py` | Long-form pages now ship from per-archive normalisers + Astro |
| `scripts/sync-nav.py` | `src/components/Nav.astro` is the single source of truth |
| `scripts/sync-footer.py` | `src/components/Footer.astro` is the single source of truth |
| `.github/workflows/sync-nav.yml` | Policed `sync-nav.py` (deleted) |
| `.github/workflows/sync-footer.yml` | Policed `sync-footer.py` (deleted) |
| `.github/workflows/html-validate.yml` | Redundant with `quality-gates.yml` visual-regression + fidelity for our own pages; scraped upstream HTML was already path-excluded |

**Preserved by Plan 04-20 — carve-outs:**

| Path | Preservation reason |
| ---- | -------------------- |
| `scripts/spider.py` | Phase 5 SCRP scope per RESEARCH §10 |
| `scripts/build-redirects.py` | `quality-gates.yml` redirects drift gate (`--check`) is the consumer; remains useful through Phase 5/6 |
| `scripts/build-brazil.py` + `build-chile.py` + `build-geipan.py` + `build-uk.py` | `scrape.yml` consumer (Phase 5 SCRP); retire when scrape.yml is rewritten |
| `scripts/build-api.py` + `build-cases.py` + `build-feeds.py` + `build-geo.py` + `build-og.py` + `build-pages-index.py` + `build-stories.py` + `build-sw.py` + `build_batch3.py` | `scrape.yml` consumer (Phase 5 SCRP); same retirement window |
| `scripts/copy-legacy-archives.sh` | Ships 11 dormant archives + partial-port sub-pages (`aaro/<case>.html`, `nasa/story.html`, `nara/<case>.html`, `nz/*`, `uruguay/*`) into `dist/`; retired when dormant archives are hard-deleted in a future milestone |
| `scripts/normalize-*.py` | Feed Astro content collections; D-10 LOCKED contract with `Card.astro` |
| `scripts/dl-<slug>.sh` | Per-archive downloaders (D-11); Phase 5 SCRP keeps these as the cache layer |
| `scripts/verify-*.{py,sh}` | Quality-gates verifiers |

**Invariant guard:** `scripts/verify-python-retired.sh` asserts the
retired set stays deleted. Run locally before any commit that touches
`scripts/`; can be wired into CI when a regression appears.

---

## Consequences

**Positive**
- Active-surface build is now wholly owned by Astro. No dual-source-of-truth between Python builders and Astro components.
- CLAUDE.md §5/§6/§13 + §12 useful-commands updated to reflect the Astro pipeline (`pnpm build`).
- `scripts/sync.sh` rebuild block delegates to `pnpm build` instead of invoking deleted Python builders.
- Three CI workflows (sync-nav, sync-footer, html-validate) removed → faster CI matrix.
- `verify-python-retired.sh` provides a 0-cost regression guard.

**Negative / accepted risk**
- `scrape.yml` is presently broken in main: it references already-deleted `build-{aaro,nasa,nara}.py` (deleted in Plans 04-15..04-17). It runs only on the weekly Monday cron + `workflow_dispatch`; nobody depends on its output until Phase 5 reactivates scraping. Phase 5 SCRP will rewrite it end-to-end. Tracked as Phase 5 carryover, not a Phase 4 close blocker.
- `scripts/sync.sh` (legacy operator helper) still exists for offline-dev sessions; its rebuild path now points at `pnpm build`. Will be deprecated entirely once Phase 5 SCRP lands the new scrape pipeline.
- The 11 dormant `build-<slug>.py` (brazil, chile, geipan, uk) are dead code from the active-surface POV but kept alive by the still-broken `scrape.yml`. This is intentional asymmetry — deleting them while scrape.yml still references them would force a scrape.yml rewrite into Phase 4, which is out of scope.

**Neutral**
- Hard-deleting the 11 dormant archives (and the dl/normalize/scrape scripts that feed them) is a separate decision deferred to a future milestone (see CLAUDE.md §2 status table + 04-SCOPE-PIVOT-SUMMARY).

---

## Verification

```bash
bash scripts/verify-python-retired.sh
# Expected: "verify-python-retired.sh: OK — Python build retirement invariant holds (...)"
# Exit 0 on success; exit 1 if any retired script reappears.
```

LHCI HARD assertions live in `.lighthouserc.cf.json` and are enforced
by `.github/workflows/quality-gates.yml` lighthouse job (now without
`continue-on-error`).
