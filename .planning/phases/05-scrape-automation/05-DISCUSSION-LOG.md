# Phase 5: Scrape Automation — Discussion Log

> **Audit trail only.** Decisions captured in 05-CONTEXT.md; this log preserves the conversation.

**Date:** 2026-05-28
**Phase:** 05-scrape-automation
**Mode:** discuss (default)

## Pre-Discussion State

**Carryover from Phase 4:**
- R2 binary CDN live at assets.realufo.org (Plan 04-02 + scope-pivot)
- `scripts/_archive_common.rewrite_to_r2()` helper
- `scripts/spider.py` preserved per ADR python-build-retired (explicitly Phase 5 scope)
- 4-archive active scope (wargov + aaro + nasa + nara) per Phase 4 scope-pivot D-41
- `.github/workflows/r2-sync.yml` exists locally + UNPUSHED to remote (Frank pull-only on hectorchanht/gov-ufo-archive)
- Existing remote `scrape.yml` runs Monday 06:00 UTC cron with `|| true` failure-swallowing (SCRP-08)
- Phase 4 UAT R2 bulk-migration deferred — operator was given PATH A (push r2-sync.yml + trigger) and PATH B (operator-direct wrangler put loop)

**SCRP requirements scoped:** SCRP-01..10 (10 reqs).

## Round 1 — 4 gray areas presented

### Q1: Scrape architecture
- Options: Workers + GH Actions hybrid / Workers only / GH Actions only
- **User chose:** Workers cron + GH Actions hybrid (matches SCRP-01+02 roadmap)
- Locked as D-01..04

### Q2: Binary storage path
- Options: R2 primary + GH Releases archived / R2 staging→GH Releases promotion hybrid / GH Releases only
- **User chose:** Hybrid R2 staging + promote to GH Releases (matches SCRP-03/06 verbatim)
- Locked as D-05..09

### Q3: First-run bulk migration
- Options: Phase 5 entry plan / Workers cron back-fill / off-phase operator action
- **User chose:** Fold into Phase 5 entry plan
- Locked as D-13..15

### Q4: Active scrape scope
- Options: 4 active only / all 15 / 4 + opt-in dormant
- **User chose:** 4 active only (wargov, aaro, nasa, nara)
- Locked as D-10..12

## Round 2 — 4 sharp follow-ups

### Q5: Cron frequency
- Options: Weekly Monday 06:00 UTC / Daily / On-demand only
- **User chose:** Weekly (preserve existing scrape.yml cadence)
- Locked as D-02

### Q6: R2 staging layout
- Options: Same `realufo` + `staging/` prefix / Separate `realufo-staging` bucket
- **User chose:** Same bucket + staging/ prefix
- Locked as D-06

### Q7: Akamai-blocked source determination
- Options: Spike test + ADR / Skip test + assume all use GH Actions
- **User chose:** Spike test + akamai-spike.md ADR
- Locked as D-03

### Q8: Push r2-sync.yml strategy
- Options: Rewrite as part of Phase 5 entry plan / Push as-is + Workers cron on top
- **User chose:** Rewrite as part of Phase 5 entry plan
- Locked as D-14

## Claude's Discretion (no follow-up needed)

- Worker source language (TypeScript via wrangler init)
- KV namespace name (SCRAPE_STATE)
- ETag vs content-hash fingerprint mechanics
- release-upload.py retry/backoff semantics
- Spike Worker hostname (throwaway worker on realufo CF account)
- Parallel vs serial scrape lanes (measure during spike)

## Deferred Ideas

| Idea | Reason | Phase |
|------|--------|-------|
| Real-time RSS scrape triggers | Weekly cron sufficient for gov source cadence | Future milestone |
| Dormant 11-archive re-activation | Scope-pivot D-41; preserved as code, not in cron | Future milestone |
| DR restore-from-GH-Releases drill | Post-cutover concern | Phase 6 or later |
| Per-asset content-hash diff layer | ETag-only sufficient per D-01; revisit if false-negatives | Phase 5 close or later |
| Parallel scrape lanes in one Worker invocation | Measure during akamai spike | Plan 05-02 discretion |
| Frank permanent write on hectorchanht repo | Operational | n/a |

## GH Repo Access Carryover (surfaced as D-21 in CONTEXT)

All Phase 4 commits sit on LOCAL `main` only — Frank lacks push to hectorchanht. Plan 05-01's first task is the operator-gate where Hector pulls + pushes the entire Phase 4 commit chain before any Phase 5 workflow lands on remote. Without it, `gh workflow run r2-sync.yml` fails with "workflow not found".

## Source Material

- ROADMAP.md §Phase 5 (10 requirements + dependencies)
- REQUIREMENTS.md lines 74-83 (SCRP-01..10 detail)
- PROJECT.md §Active SCRAPE-02 + SCRAPE-03
- Phase 4 04-CONTEXT.md D-01..D-42
- Phase 4 04-02-SUMMARY.md (R2 mechanics + _archive_common.py)
- Phase 4 04-20-SUMMARY.md (Python retirement boundary)
- Phase 4 04-UAT.md §1 (R2 bulk migration runbook)
- ADR `.planning/decisions/r2-setup.md`
- ADR `.planning/decisions/python-build-retired.md`
- CLAUDE.md §5.1 + §5.2 + §11
- Existing `.github/workflows/scrape.yml` (preserve cron line; rewrite job body)
- Existing `.github/workflows/r2-sync.yml` LOCAL (rewrite per D-14)
- `scripts/spider.py` + `scripts/dl-*.sh` (Phase 5 scope per ADR)
