# Phase 3: SSG Foundation — Discussion Log

> **Audit trail only.** Canonical decisions in `03-CONTEXT.md`.

**Date:** 2026-05-25
**Phase:** 03-ssg-foundation
**Mode:** discuss (default)
**Areas discussed:** Data extraction · URL structure · Card pre-render strategy · Build coexistence · Layout granularity · JS invariants port · Search behavior · Fidelity strictness

User invocation: `/gsd:discuss-phase 3`. Phase 2 just shipped (CF Pages project + 60 baselines + 115 fidelity samples + all CI gates).

## Areas discussed

| Question | Selection |
|---|---|
| Data extraction — `<script id="arch-data">` → `data/<slug>.json` | **Build from CSV directly** (content-collection loader normalizes; reuses Python normalize logic) |
| wargov URL structure | **Keep `/` for wargov** (per CLAUDE.md §2 + URL-CONTRACT.txt; NO drift) |
| Card pre-render strategy | **Pre-render first 50 + lazy-load rest** (proves Phase 4 PERF-01 shard pattern on smaller wargov) |
| Build coexistence | **Astro `dist/` is CF Pages output, Python outputs stay tracked but ignored** (two origins coexist until Phase 6) |
| Layout granularity | **4 components: RootLayout + BaseHead + Nav + Footer** (standard Astro pattern per SC#3) |
| JS invariants port | **`<script is:inline>` in shared layout components** (zero hydration; survives JS-off) |
| Search on wargov | **No search yet** (Pagefind = Phase 4 SRC-01) |
| Fidelity strictness | **Byte-exact required** (D-20 Phase 2 invariant honored; smartypants BANNED for archive cards) |

## Notable decisions

- **D-01 Build from CSV** vs HTML extraction — long-term cleaner; Phase 4 14-archive port uses same logic without rewrite.
- **D-08 50-card + lazy-load** — establishes the pattern Phase 4 PERF-01 will apply at GEIPAN scale (3.3 MB inline). Proven cheap on wargov first.
- **D-23 No framework islands** — locks in vanilla `<script is:inline>` for full migration. Avoids hydration debt accumulating in Phase 4.
- **D-28 Smartypants BANNED for cards** — prevents Pitfall #6 markdown typographer drift wrecking 115-sample fidelity contract.
- **D-29 Astro 5.18.x pinned** — planner re-verifies astro#15684 status during planning; may upgrade if fixed.

## Deferred ideas (out of Phase 3 scope)

- Astro Server Islands — no hydration this phase
- MDX for cards — banned per D-28; prose-only in Phase 4
- Pagefind / injectManifest SW / self-hosted fonts / GEIPAN shard / 14-archive port — Phase 4
- sync-nav.py / sync-footer.py retirement — Phase 4 SSG-10
- CF Pages git-integration UI click — operator follow-up from Phase 2 02-01

## Claude's discretion

- Zod schema shape (union vs discriminated union vs variant)
- TypeScript vs Python for CSV normalizer
- Lazy-load trigger (IntersectionObserver vs filter-event vs idle)
- Card shard size tuning beyond initial 50
- `@astrojs/cloudflare` adapter version
- Style strategy (scoped Astro vs single global)

---

*Phase: 03-ssg-foundation*
*Discussion logged: 2026-05-25*
