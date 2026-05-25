# Phase 2: Infrastructure & CI Scaffolding — Discussion Log

> **Audit trail only.** Canonical decisions in `02-CONTEXT.md`.

**Date:** 2026-05-25
**Phase:** 02-infrastructure-ci-scaffolding
**Mode:** discuss (default)
**Areas:** CF Pages deploy · Workers Paid · `_headers` CSP · Playwright baselines · `_redirects` source · CI workflow shape · Fidelity sample scope · Budget enforcement

User invocation: `/gsd:do "what next, i really want the astro or 11ty done fast"` → routed via `/gsd:do` → `/gsd:discuss-phase 2`. Decision: Phase 2 (infra) is prereq to Phase 3 (Astro install). Fast SSG path requires Phase 2 first.

## Areas discussed

| Question | Selection |
|---|---|
| CF Pages deploy connection? | CF git integration (recommended) |
| Playwright baselines source? | Capture vs live realufo.org |
| `_headers` CSP strictness? | **Skip CSP for Phase 2** (defer to Phase 6) |
| Workers Paid activation? | Operator activates ASAP ($5/mo) |
| `_redirects` source? | Auto-generate from URL-CONTRACT.txt |
| CI workflow structure? | Single workflow, parallel jobs |
| Fidelity sample scope? | Hero ledes + FAQ answers + license footers + official titles |
| Budget enforcement? | Visual + fidelity hard; perf soft (warn) until Phase 4 close |

## Notable user redirect

User chose **skip CSP for Phase 2** — this is a sensible call given current site has heavy inline JS that strict CSP would break. CSP migrates to Phase 6 (cutover phase) where SSG markup is settled.

## Deferred ideas

- Cross-browser visual matrix (Firefox + WebKit) — defer to Phase 4
- CSP enforcement — Phase 6
- HSTS preload — Phase 6
- Hard-fail Lighthouse budgets — Phase 4 close
- PR comment bot for visual diffs — optional polish
- R2 for baseline storage — overkill at current scale

## Claude's discretion

- Helper script filenames
- Tone-colour test language (Python vs Playwright JS)
- GH Actions runner choice
- Lighthouse-CI action version
- Playwright config sharing strategy

---

*Phase: 02-infrastructure-ci-scaffolding*
*Discussion logged: 2026-05-25*
