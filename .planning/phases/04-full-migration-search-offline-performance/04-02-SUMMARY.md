---
phase: 04-full-migration-search-offline-performance
plan: "02"
subsystem: infrastructure
tags: [r2, binary-cdn, cloudflare, cors, rclone, gh-actions, infrastructure]
status: in-progress
requires:
  - "Plan 02-01 cf-pages-project.md (CF account + CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID secrets)"
  - "Plan 03-03 normalize-csv.py + data/wargov.json + shard scheme (extended by Task 3)"
  - "scripts/snapshot-urls.py:slugify (byte-equivalent port lives in _archive_common.py)"
provides:
  - "scripts/_archive_common.py — rewrite_to_r2 + slugify helpers (consumed by Wave 3+ archive normalisers)"
  - ".planning/decisions/r2-setup.md — 5th ADR locking R2 bucket name, custom domain, CORS scope, GH secrets, A3 thumbnail decision"
  - ".github/workflows/r2-sync.yml — rclone S3-compat sync of PDFs/videos to R2 on push + workflow_dispatch"
  - "tests/r2-urls.spec.ts — Playwright HEAD-check sample of card.url R2 URLs"
  - "data/wargov.json + shards regenerated with R2 URLs in card.url field (PDFs + videos only; images preserved verbatim)"
affects:
  - "All Wave 3+ archive port plans (04-05..04-18) — must `from _archive_common import rewrite_to_r2` to emit R2 URLs"
  - "Plan 04-04 wargov repaging — consumes the R2-URL wargov.json + shards regenerated here"
  - "Operator follow-up: `gh workflow run r2-sync.yml -f full_sync=true` after merge triggers bulk migration of 165 PDFs + 60 videos"
tech-stack:
  added:
    - "rclone (installed via curl https://rclone.org/install.sh in GH Actions, not committed to repo)"
  patterns:
    - "Shared helper module scripts/_archive_common.py for cross-archive normaliser logic (replaces 14× duplicated slugify + R2 URL routing)"
    - "Image extension allowlist (.png/.jpg/.webp/.svg/.avif/.bmp) preserved as-is by rewrite_to_r2 — thumbs stay local per D-01 refinement + Pitfall #7"
    - "rclone S3-compat with --checksum + concurrency.cancel-in-progress:false for idempotent incremental sync"
key-files:
  created:
    - "scripts/_archive_common.py — rewrite_to_r2(local_path, archive_slug, asset_type) + slugify(text)"
    - ".planning/decisions/r2-setup.md — 5th ADR (bucket + CORS + secrets + A3)"
    - ".github/workflows/r2-sync.yml — TBD Task 3"
    - "tests/r2-urls.spec.ts — TBD Task 3"
  modified:
    - "scripts/normalize-csv.py — TBD Task 3 (call rewrite_to_r2 for PDF/VID Type rows)"
    - "data/wargov.json + data/wargov-shard-{2..5}.json + public/data/* — TBD Task 3 (regenerated post-edit)"
decisions:
  - "D-01 (refined): PDFs + videos migrate to R2; thumbs stay local (Astro Image processes local files only per Pitfall #7)"
  - "D-02: assets.realufo.org custom domain via CF dashboard (proxied CNAME); never reference *.r2.dev"
  - "D-04: rclone S3-compat sync for bulk migration (checksum-based idempotency for free)"
  - "D-05: single bucket `realufo`, prefix layout pdfs/<slug>/ + videos/<slug>/"
  - "D-24: CORS scope explicit allowlist (realufo.org + *.realufo.pages.dev + localhost dev); GET+HEAD only; no wildcard origin"
  - "Two-token model: CLOUDFLARE_API_TOKEN (wrangler bearer) + CLOUDFLARE_R2_ACCESS_KEY/SECRET_KEY (rclone S3-compat) — both kept; different auth surfaces"
  - "Jurisdiction: Global (public-domain content, no FedRAMP/EU constraint)"
  - "r2-cors.json schema preserved as committed at e9ff48c (wrangler 4.x lowercase keys); operator already applied + verified — regenerating would break working CORS"
requirements: [SSG-06]
metrics:
  duration: TBD
  tasks_completed: TBD
  commits: TBD
  files_created: TBD
  files_modified: TBD
  completed: "2026-05-27"
---

# Phase 4 Plan 02: Cloudflare R2 binary CDN setup Summary

**Skeleton (Task 2 commit landed at `53110d1`); Task 3 in-flight. This document
will be finalised after Task 3 commits.**

Stands up Cloudflare R2 as the canonical binary CDN at `assets.realufo.org`,
extends `scripts/normalize-csv.py` to emit R2 URLs in card.url fields, and
ships the GH Actions workflow that keeps the bucket in sync with the repo's
binary inventory. Provides `scripts/_archive_common.py rewrite_to_r2()` as the
shared URL-rewrite helper consumed by all Wave 3+ per-archive normalisers.

## Status placeholder

| Task | Hash | Status |
|------|------|--------|
| Task 1 (operator: bucket create + CORS apply + custom domain bind + GH secrets) | n/a | DONE pre-spawn (orchestrator) |
| Task 2 (rewrite_to_r2 + ADR) | `53110d1` | DONE |
| Task 3 (normalize-csv extension + r2-sync.yml + Playwright spec) | TBD | IN-PROGRESS |
| Task 4 (operator-triggered bulk migration) | n/a | DEFERRED (operator triggers post-merge) |

## Self-Check: PENDING (will run after Task 3 commits)
