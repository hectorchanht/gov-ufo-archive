# Phase 1: Pre-Migration Safety — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Canonical decisions live in `01-CONTEXT.md` — this log preserves the conversation.

**Date:** 2026-05-25
**Phase:** 01-pre-migration-safety
**Mode:** discuss (default, standard mode)
**Areas discussed:** URL-CONTRACT format & scope · SW kill-switch strategy · Akamai spike methodology · CLAUDE.md refresh scope

User invocation: `/gsd:discuss-phase 1 update claude.md too` — explicit ask to fold CLAUDE.md update into Phase 1 work.

## Area 1: URL-CONTRACT format & scope

| Question | Options presented | User selection |
|---|---|---|
| What counts as a URL? | Routes + #card-<id> (rec) / Routes only / Routes + named anchors | **Routes + #card-<id> anchors** |
| Format? | Plain text (rec) / JSON / sitemap.xml | **Plain text, one URL per line** |
| Generator? | Python script (rec) / Shell+grep / wget --spider crawl | **Python script** (`scripts/snapshot-urls.py`) |

**Notes:** CI gate against drift is Phase 2 work; Phase 1 just produces the artifact.

## Area 2: SW kill-switch strategy

| Question | Options presented | User selection |
|---|---|---|
| Kill-switch behavior? | Full nuke (rec) / Unregister only / Stale-but-readable | **Full nuke** — unregister + caches.delete + clients.postMessage + skipWaiting |
| Coexist with existing sw.js? | Replace in-place (rec) / Sidecar at /sw-kill.js | **Replace in-place** at `/sw.js` |
| Self-disable after N days? | No timer (rec) / Auto-empty after 14d / Aggressive self-uninstall | **No timer** — replaced by real SW on Phase 6 cutover |

**Notes:** 14-day cutover gate measures from kill-switch deploy date, not from install date in user browsers.

## Area 3: Akamai spike methodology

| Question | Options presented | User selection |
|---|---|---|
| Probe scope? | war.gov+aaro.mil only (rec) / All 15 / war.gov+aaro.mil + 3 random | **war.gov+aaro.mil + 3 random samples** |
| Probe methodology? | Bilateral 100 reqs (rec) / Single-shot smoke / Bilateral with curl_cffi | **Bilateral, 100 reqs each over 1 hr** |
| Pass/fail threshold? | ≥95% OR Workers wins (rec) / Strict 100% / Compare absolute counts | **≥95% 200s AND ≥ Actions success rate** |
| Where to record? | `.planning/decisions/akamai-spike.md` (rec) / phase-local | **`.planning/decisions/akamai-spike.md`** — new ADR folder |

**Notes:** Decision is per-source (Workers may be viable for some sources, not others). Phase 5 architects hybrid based on outcome.

## Area 4: CLAUDE.md refresh scope

| Question | Options presented | User selection |
|---|---|---|
| Refresh scope? | Sectional updates (rec) / Full regen via gsd-sdk / Sectional + GSD note | **Sectional updates** — three edits |
| Mark old design as 'starting point'? | Header note in §3 (rec) / Leave as-is / Annotate every section | **Header note** at top of §3 |
| Add SSG Migration section? | Yes, short pointer (rec) / No | **Yes** — new §13 SSG Migration in Progress |

**Notes:** Sectional approach applied AS PART OF this phase's commit (not deferred to plan-phase): §3 header note added, §5.1 URL pattern fixed (PMS-06 closed in-discussion), §13 new section appended.

## CLAUDE.md edits applied inline during discussion

Three concrete edits to `CLAUDE.md` (committed alongside this discussion's CONTEXT + LOG):

1. **§3 Design system header note** — visual identity locked, markup may evolve under SSG migration.
2. **§5.1 URL pattern** — `hectorchanht/war-gov-ufo-release` → `hectorchanht/gov-ufo-archive` (PMS-06 closed).
3. **§13 SSG Migration in Progress (new section)** — points at `.planning/PROJECT.md`, `ROADMAP.md`, `REQUIREMENTS.md`, `research/SUMMARY.md`; documents target stack and house-rule survivability.

## Deferred ideas (captured during discussion)

- CI gate diffing URL-CONTRACT.txt against PR builds → Phase 2 (INF-02)
- `sitemap.xml` alternative format → backlog (post-SSG)
- Per-archive Akamai spike for all 15 source domains → conditional Phase 5 sub-task
- Annotating every CLAUDE.md section with LOCKED/EVOLVING markers → revisit at Phase 4 close

## Claude's discretion (not asked, not pre-decided)

- Exact filename of URL snapshot script
- HTML parsing strategy (BeautifulSoup vs `re` vs lxml)
- Kill-switch SW banner comment wording
- Spike code location (`.planning/spikes/01-akamai/` recommended in CONTEXT.md §specifics)

---

*Phase: 01-pre-migration-safety*
*Discussion logged: 2026-05-25*
