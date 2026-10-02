---
phase: quick-261001-q6n
plan: 01
subsystem: hosting
tags: [domain, seo, cors, cloudflare-pages]
requires: []
provides: [release.realufo.org canonical origin]
affects: [canonical, og:url, sitemap, robots, feeds, SW scope, tests, workflows, watchdog, r2-cors]
tech-stack:
  added: []
  patterns: []
key-files:
  created: []
  modified: [CNAME, r2-cors.json, astro.config.mjs, public/robots.txt, workers/watchdog/wrangler.toml, tests/r2-urls.spec.ts, README.md, SECURITY.md, CLAUDE.md, "~124 other tracked text files"]
decisions:
  - "Self-origin is https://release.realufo.org; apex realufo.org stays only as brand text, emails, Atom tag: IDs, CHANGELOG and .planning/"
  - "r2-cors.json keeps https://realufo.org alongside the release origin (the apex Worker may still fetch R2)"
metrics:
  duration: ~10 min
  completed: 2026-10-01
---

# Quick 261001-q6n: Host this repo as release.realufo.org Summary

Every absolute `https?://realufo.org` self-URL in 131 tracked text files (717 occurrences) now points at `https://release.realufo.org`; CNAME, CORS allow-list and hosting docs updated; `pnpm build` green with a clean dist/.

## Tasks

| Task | Name | Commit |
| --- | --- | --- |
| 1 | Mechanical URL rewrite + CNAME + r2-cors.json | c636d8f |
| 2 | Hosting docs: README, SECURITY, CLAUDE | ea444a0 |
| 3 | Build and verify dist/ origin | (verification only, no commit) |

## Verification (observed)

- Task 1: after the rewrite, the only tracked file outside CHANGELOG/.planning/CSVs that still contains `https?://realufo.org` is `r2-cors.json`. That one is intentional: it keeps the apex CORS origin. CNAME = `release.realufo.org`. astro.config.mjs:167 `site: 'https://release.realufo.org'`. CORS JSON parses and lists both origins. Collateral counts match the baseline: `assets.realufo.org` files 87 -> 87, `tag:realufo.org` in feeds/all.xml 100 -> 100, security@/conduct@ files 4 -> 4, `og:site_name" content="realufo.org"` files 76 -> 76. Zero `release.release.` double-rewrites. No diff under .planning/, CHANGELOG.md, or the CSVs.
- Task 2: plan automated gate printed OK.
- Task 3: `pnpm build` exit 0 (sitemap 67 urls). `grep -rIl -E 'https?://realufo\.org' dist/` = 0. dist/index.html canonical = `https://release.realufo.org/`. dist/robots.txt `Sitemap: https://release.realufo.org/sitemap.xml`. dist/sitemap.xml has 67 release-origin URLs and 0 apex URLs.

## Deviations from Plan

**1. [Rule 1 - Bug] Plan's exclusion regex did not exclude .planning/ files**
- `grep -zv -E '^(CHANGELOG\.md|\.planning/|.*\.csv)$'` anchors `\.planning/` with `$`, so it matches only the literal path `.planning/` and lets every `.planning/**` file through. I used git pathspec exclusions instead: `git ls-files -z -- . ':!CHANGELOG.md' ':!.planning' ':!*.csv'`. Same 131-file candidate set, and .planning/ was verifiably untouched.

**2. [Rule 3 - Blocking] Rewrite run as one perl script over a file list**
- The sandbox rejected `xargs -0 perl -pi`, so one perl script read the NUL-safe candidate list and ran the same substitution `s#https?://realufo\.org#https://release.realufo.org#g`.

**3. [Rule 1 - Bug] Re-added the apex CORS origin after the global rewrite**
- The global rewrite turned the existing `"https://realufo.org"` entry in r2-cors.json into the release origin. I then inserted `"https://realufo.org"` above it so both origins are present, as the plan requires. Because of this, the plan's own "zero files" gate can't pass literally: r2-cors.json has to keep the apex string. The gate needs r2-cors.json excluded.

**4. [Rule 1 - Bug] Kept the http scheme in a redirect comment**
- Line 28 of `.github/workflows/quality-gates.yml` describes an `http://` -> 301 redirect. The rewrite forced it to `https://`, which changed what the comment says. I restored it as `http://release.realufo.org/...`.

**5. Baseline drift**
- The plan expected 86 `assets.realufo.org` files; the actual baseline was 87 (the new PLAN.md also mentions it). The count is unchanged after the rewrite, which is what the no-collateral check is for.

**6. Build setup**
- node_modules was missing in the worktree, so I symlinked it from the main checkout for the build and removed it afterwards. Nothing extra was committed, and dist/ is gitignored.

## Notes

- `tests/visual-baselines/README.md` still says "GitHub Pages origin" in historical D-12 prose. Only its URL was rewritten, which keeps this change to URLs only.
- Not done here (orchestrator steps): attach `release.realufo.org` as a custom domain on CF Pages project `realufo` plus the DNS record, and apply `r2-cors.json` to the live bucket.

## Self-Check: PASSED

- CNAME, r2-cors.json, README.md, SECURITY.md, CLAUDE.md modified and present
- Commits c636d8f, ea444a0 exist on branch worktree-agent-a51147928dbf17d8d
