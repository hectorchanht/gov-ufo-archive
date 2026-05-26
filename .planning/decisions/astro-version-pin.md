# Astro Version Pin Decision — realufo SSG migration

Fourth ADR-style decision document under `.planning/decisions/` (after
`akamai-spike.md`, `dns-ttl.md`, `cf-pages-project.md`, `workers-paid.md`).
Records the Astro framework + Cloudflare adapter version pinned during
Phase 3 SSG foundation, the re-verification of astro#15684 (the historical
trigger for the defensive pin), and the explicit revisit point at the
close of Phase 4.

## Status

`accepted` — proposed 2026-05-25 (Phase 3 kickoff), accepted 2026-05-25
(Phase 3 Plan 03-01 Task 1). Transitions: `proposed → accepted (2026-05-25)
→ revisit at Phase 4 close`. The revisit is not a re-decision — it is a
scheduled re-evaluation gate that may either confirm the existing pin,
tighten it to a newer 5.x patch line, or (only if the conditions in
`## Future-phase hooks` below are all met) propose moving to a 6.x line in
a new ADR.

## Decision

Pin `astro` to **`~5.18.0`** (tilde patch-only) in
`package.json#dependencies`, and pin `@astrojs/cloudflare` to the
compatible 5.x adapter version range (the v12.6.x line, which declares
`astro: ^5.7.0` in `peerDependencies`). Defer any move to Astro 6.x and
the matching `@astrojs/cloudflare` 13.x adapter to the close of Phase 4
SSG migration once wargov + the 14-archive port + Pagefind + injectManifest
service worker have all shipped and proven stable on Cloudflare Pages.

## Context

The pin was introduced defensively in research/STACK.md based on
[astro#15684](https://github.com/withastro/astro/issues/15684) — "Astro v6
Cloudflare prerendering environment is too restrictive" — a regression
that broke `@astrojs/cloudflare`'s prerender step inside Astro 6's workerd
build environment. At the time research was written, this issue was open
and was the dominant reason to avoid Astro 6.

Re-verified during Phase 3 Plan 03-01 Task 1: **issue #15684 is now
CLOSED** (closed 2026-03-11). The fix landed upstream — the linked
resolution PR in the Astro repository tightened the workerd build context
so the prerender step succeeds. As of mid-2026 the 6.x line carries the
fix. The narrow regression that originally drove the defensive pin is
resolved.

However, the 5.x → 6.x jump is not a single closed bug. Astro 6.x also
shipped a number of unrelated breaking changes that interact with this
project's downstream Phase 3 / Phase 4 work:

- **Zod 3 → Zod 4 bump.** Per research/STACK.md §"Version Compatibility",
  Astro 6 takes Zod 4 as its content-schema dependency. Plan 03-02
  (Content Collections schema) commits the project to Zod 3 in
  `src/content.config.ts`. A move to Astro 6 in mid-Phase-3 would require
  rewriting any Zod-3-specific schema work introduced in 03-02 + 03-03
  for Zod 4. The migration cost is not unbounded, but it is non-zero for
  a solo maintainer.
- **Content Layer API shifts.** Astro 6 continued to evolve the content
  layer (file loaders, glob loaders) past the Astro 5 surface. Plan 03-02
  hardens against the Astro 5 surface specifically — any rewrite to 6.x
  needs to re-verify the `file()` loader contract.
- **Adapter family compatibility window.** `@astrojs/cloudflare@13.x` has
  `astro: ^6.3.0` in peerDependencies; jumping to Astro 6 requires
  jumping the adapter at the same time. Compounding two version-pin
  changes inside a single phase is a brownfield migration anti-pattern.

The risk profile for this project — solo maintainer, brownfield big-bang
migration, 14 unported archives still ahead, the entire Phase 4 SW + SRC +
PERF work still ahead — argues for ONE framework version transition,
sequenced after the migration is otherwise stable. That gate is Phase 4
close. The defensive pin stays; the trigger changes from "astro#15684 is
open" to "Phase 4 hasn't shipped yet."

## Alternatives considered

**(a) `astro@^5` (caret).** Allows Astro 5.x → 5.99.x drift. Rejected for
two reasons. First, `^5` opens the door to whatever the highest 5.x.x
release is at any future `pnpm install --no-frozen-lockfile`, including
versions that might land late-Phase-3 with regressions of their own —
the original astro#15684 regression-class is exactly the kind of failure
mode tilde-pinning was introduced to guard against. Second, caret offers
no clear story for the Phase 4 close revisit; tilde + patch line gives a
crisper "tighten or relax" lever. The caret is the npm-ecosystem default
but is the wrong default for this project at this phase.

**(b) `astro@~5.x` (latest 5.x tilde).** As of Phase 3 Plan 03-01
execution time, `pnpm view astro versions` reports the latest stable
5.x.x as **5.18.2** (with 5.18.x patches available at .0, .1, .2). The
"latest tilde" resolution today is `~5.18.0`. This is the chosen
alternative for the Implementation section. Rejected as a NAMED
alternative because (b) is identical in effect to the chosen decision —
the difference is in how the pin string is written, not what it resolves
to. Documenting `~5.18.0` explicitly (rather than "latest 5.x tilde at
install time") gives the next planner an unambiguous historical anchor:
they can see exactly which patch line Phase 3 started on, independent
of npm registry changes between now and Phase 4 close.

**(c) `astro@~6.x.y` (move to 6.x now).** Rejected. Even with #15684 now
closed, Astro 6 introduces three additional integration costs at the
worst possible time: Zod 3 → 4 invalidates Plan 03-02 schema, Content
Layer API evolution invalidates Plan 03-02 + 03-03 loader contracts, and
the adapter must jump from 12.x → 13.x concurrently. The project's own
Phase 3 success criteria (wargov port byte-identical to today's GH Pages
output, 115/115 fidelity samples) is already a tight constraint; adding
a framework major-version transition multiplies failure modes. Defer to
a single Phase 4 close transition where Zod 3 → 4 + Content Layer API +
adapter jump can be handled in one coordinated migration ADR rather
than fragmented through Phase 3 and 4.

## Implementation

The package.json entries written in Plan 03-01 Task 2 are:

- `astro` listed in `dependencies` with the literal pin string
  `~5.18.0` (tilde, not caret, not bare). At install time `pnpm install`
  resolves this to the latest published 5.18.x patch — currently 5.18.2.
  The tilde range allows future `pnpm update` to pull 5.18.3, 5.18.4, etc.
  as Astro publishes patches, but NEVER 5.19.x, 5.20.x, or 6.x.x. The
  resolved patch is locked in `pnpm-lock.yaml` and is the version that
  CF Pages will install when running `pnpm install --frozen-lockfile`
  per D-31.
- `@astrojs/cloudflare` listed in `dependencies` with the literal pin
  string `^12.6.0`. The adapter family is more forgiving than the
  framework itself — the 12.6.x line is internally stable for the
  Cloudflare runtime semantics this project uses (static output, no
  SSR, no Worker bindings; D-12, D-23, T-03-03). The caret here is
  intentional because the adapter's peerDependencies bind it to
  `astro: ^5.7.0`, which transitively locks the adapter to the same
  5.x major family as the tilde-pinned `astro` package. A pnpm install
  with both pins in place cannot accidentally pull `@astrojs/cloudflare@13`
  without violating the peer constraint.

Installation command used at execution time (recorded for reproducibility):

```
pnpm add astro@~5.18.0 @astrojs/cloudflare@^12.6.0 zod@^3 papaparse@^5
pnpm add -D @types/papaparse@^5 typescript@~5
```

NO `--save-exact` flag on the `astro` install — the tilde is the pin; the
exact patch resolution lives in `pnpm-lock.yaml`. The dev-dependency
`typescript@~5` follows the same patch-line philosophy (Astro 5 ships
with TypeScript 5.x first-class support).

If `pnpm view astro versions` at execution time had reported NO 5.18.x
patches available, the fallback path was to pin `~5.17.0` and update this
ADR with a one-line note in `## Phase 3 invariants honored`. That
fallback was not needed: 5.18.0, 5.18.1, and 5.18.2 are all available.

## Phase 3 invariants honored

This ADR codifies the following CONTEXT.md decisions for downstream
phases:

- **D-29** — `astro` is tilde-pinned (`~5.18.0`), NOT caret. The defensive
  pin survives even though the original astro#15684 trigger has been
  upstream-resolved; the rationale has shifted from "the bug is open" to
  "the migration is mid-flight."
- **D-30** — `@astrojs/cloudflare` adapter is pinned alongside the
  framework. The chosen version (`^12.6.0`) is documented here as the
  authoritative source for any future planner asking "which adapter line
  did Phase 3 ship on."
- **D-31** — CF Pages build command remains `pnpm install --frozen-lockfile
  && pnpm prebuild && pnpm build`. `--frozen-lockfile` ensures the pin
  recorded in `pnpm-lock.yaml` is what CF actually installs; no silent
  drift to a different 5.18.x patch between local development and CI.
- **D-37** — Phase 3 makes no DNS or domain changes. The Astro install is
  invisible to `realufo.org` end-users until Phase 6 cutover.
- **D-39** — Phase 3 does NOT delete or modify the existing Python build
  scripts under `scripts/build-*.py`. Astro + Python coexist on the
  `ssg-migration` branch throughout Phase 3 + Phase 4.

## Future-phase hooks

At **Phase 4 close**, after all of the following have shipped and proven
stable on Cloudflare Pages preview deployments:

1. All 14 non-wargov archives ported to Astro (SSG-06)
2. Pagefind 1.x replacing Lunr at `/search.html` (SRC-01..02)
3. `@vite-pwa/astro` `injectManifest` SW registered via `BaseHead.astro`
   on every page (SW-01..03)
4. PERF-01 GEIPAN-style shard refactor proven viable (or explicitly
   deferred)

…draft a follow-up ADR `astro-6-migration.md` that captures:

- Current Astro 5 patch line at the revisit point (will be later than
  5.18.2 by then; tilde-resolution will have pulled forward)
- Current Astro 6 latest minor/patch
- Zod 3 → 4 migration cost estimate against the *as-shipped* Phase 4
  schema (Plan 03-02 schema may have been extended through Phase 4)
- Content Layer API surface diff between the as-shipped 5.x usage and 6.x
- Whether `@astrojs/cloudflare` 13.x has accumulated any of its own
  regressions over the same time window (mirror the astro#15684
  re-verification methodology against that adapter's open issues)
- Recommended cut-over plan (rebase branch + 24-hour soak on CF Pages
  preview before merging to `ssg-migration`)

If conditions 1-4 above are NOT all met at Phase 4 close, this ADR's
decision automatically rolls forward to Phase 5 close, then Phase 6 close.
There is no scheduled time-based expiry — the gate is "migration is
otherwise stable", not "N months have elapsed."

## References

- [astro#15684 — v6 Cloudflare prerendering environment is too restrictive](https://github.com/withastro/astro/issues/15684) (closed 2026-03-11; the historical trigger for this pin, now upstream-resolved)
- `.planning/research/STACK.md` §"Major version risks" + §"Version Compatibility" — original recommendation to pin `~5.x.y`
- `.planning/research/PITFALLS.md` §Pitfall #6 — markdown typographer drift (intersects D-28 ban on smartypants for archive card content; pin survives partly because the typographer-drift mitigation is encoded against the Astro 5 surface in `astro.config.mjs`)
- `.planning/phases/03-ssg-foundation/03-CONTEXT.md` D-29..D-31, D-37, D-39 — decisions this ADR codifies
- `.planning/decisions/cf-pages-project.md` §"Future-phase hooks" — notes Phase 3 (Astro install) edits the build command + output dir; this ADR is the sibling that locks the framework version
