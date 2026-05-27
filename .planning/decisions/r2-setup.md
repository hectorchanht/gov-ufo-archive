# R2 Setup Decision — realufo binary CDN

Fifth ADR-style decision document under `.planning/decisions/` (after
`akamai-spike.md`, `dns-ttl.md`, `cf-pages-project.md`,
`astro-version-pin.md`, `workers-paid.md`). Records the Cloudflare R2
bucket, custom-domain bind, CORS scope, and GH Actions secrets shipped
in Phase 4 plan `04-02-r2-setup` — the canonical binary CDN for every
PDF + video served by realufo.org.

## Status

`bucket-created-cors-verified-bulk-migration-pending` — bucket
`realufo` exists in account `f1868a071996e836eae6da2b65f37929`, custom
domain `assets.realufo.org` is bound (proxied CNAME via CF dashboard),
CORS rules from `r2-cors.json` were applied via
`wrangler r2 bucket cors set realufo --file ./r2-cors.json --force` at
plan-execute time. R2 API token + GH Actions secrets are in place. The
**first-run bulk migration** of the 165 PDFs + 60 videos from
`pdfs-v1`/`videos-v1` GH Releases tags is deferred — operator triggers
via `gh workflow run r2-sync.yml -f full_sync=true` after this plan
merges to main. Transitions:
`bucket-created-cors-verified-bulk-migration-pending` → `bulk-migrated`
(operator triggers workflow_dispatch) → `serving-prod`
(Phase 6 DNS cutover; bucket already live, only the root-domain page
references shift).

## Bucket identity

- **Cloudflare account ID:** `f1868a071996e836eae6da2b65f37929` (user
  `f147259@gmail.com`)
- **R2 bucket name:** `realufo` (single bucket — D-05, prefix-based
  layout for all 15 archives)
- **Bucket creation method:** `wrangler r2 bucket create realufo`
  (executed by operator at plan-execute time, see operator note below)
- **Jurisdiction:** Global (no region pin). No FedRAMP / EU compliance
  constraint — content is public-domain government UAP records (USA
  17 U.S.C. § 105 + per-jurisdiction equivalents per CLAUDE.md §9).
  Global keeps egress free across CF's anycast PoPs.
- **Storage tier:** Standard. No infrequent-access tier needed — all
  objects are hot from public reads.
- **Custom domain:** `assets.realufo.org` (D-02). Proxied CNAME in
  `realufo.org` zone (orange-clouded per CF requirement for R2
  custom domains). Dashboard-bound at
  `https://dash.cloudflare.com/f1868a071996e836eae6da2b65f37929/r2/default/buckets/realufo`
  → Settings → Custom Domains → Connect Domain.
- **Public access:** Via custom domain only. The `*.r2.dev` URL is
  NEVER referenced from cards or normalisers — per D-02 the custom
  domain is the stable URL contract (survives bucket regeneration via
  DNS swap).

## Object layout (D-05 — single-bucket prefix scheme)

```
realufo/
├── pdfs/
│   ├── wargov/   ← 116 PDFs (initial bulk; ~165 total across all archives)
│   ├── aaro/
│   ├── nasa/
│   ├── nara/
│   ├── geipan/
│   ├── uk/
│   ├── brazil/
│   ├── chile/
│   ├── argentina/
│   ├── canada/
│   ├── italy/
│   ├── nz/
│   ├── peru/
│   ├── spain/
│   └── uruguay/
└── videos/
    ├── wargov/   ← 60 mp4 (initial bulk)
    ├── aaro/
    └── ... (per-archive prefixes populated as Wave 3+ ports land)
```

**Thumbnails do NOT live in R2.** A3 LOCKED — see "A3 decision" below.

## URL contract

The custom-domain URL pattern emitted by `scripts/_archive_common.py
rewrite_to_r2()` and consumed by `scripts/normalize-csv.py` + (Wave 3+)
per-archive normalisers:

```
https://assets.realufo.org/pdfs/<archive_slug>/<basename>
https://assets.realufo.org/videos/<archive_slug>/<basename>
```

Examples:

```
https://assets.realufo.org/pdfs/wargov/18_100754_general_1946-7_vol_2.pdf
https://assets.realufo.org/videos/wargov/PR50_4UAP_Formation_Iran.mp4
https://assets.realufo.org/pdfs/aaro/2024-AARO-historical-record-vol-1.pdf
```

The basename is computed as `local_path.rsplit('/', 1)[-1]` — any
upstream prefix (`bundles/Release_1/`, `https://www.war.gov/medialink/
ufo/release_1/`, `aaro/bundles/`) collapses to the filename. This
keeps R2 keys identical regardless of where the source CSV / scraper
stashed the local copy.

## CORS scope (D-24 + r2-cors.json)

Applied via `wrangler r2 bucket cors set realufo --file
./r2-cors.json --force` at plan-execute time. The file uses the
wrangler 4.x lowercase-key schema:

```json
{
  "rules": [
    {
      "allowed": {
        "origins": [
          "https://realufo.org",
          "https://*.realufo.pages.dev",
          "https://realufo.pages.dev",
          "http://localhost:4321",
          "http://localhost:8788"
        ],
        "methods": ["GET", "HEAD"],
        "headers": [
          "Range",
          "If-Match",
          "If-None-Match",
          "If-Modified-Since",
          "If-Unmodified-Since"
        ]
      },
      "exposeHeaders": [
        "Content-Length",
        "Content-Range",
        "Content-Type",
        "ETag",
        "Last-Modified"
      ],
      "maxAgeSeconds": 86400
    }
  ]
}
```

### Allowed origins — explicit allowlist, no wildcard

- `https://realufo.org` — production root (Phase 6 cutover target).
- `https://*.realufo.pages.dev` — per-deployment + per-branch preview
  URLs from Cloudflare Pages (D-31 wires `quality-gates.yml` to read
  `deployment_status.environment_url` from these).
- `https://realufo.pages.dev` — production preview branch
  (`ssg-migration`) URL.
- `http://localhost:4321` — Astro dev server (`astro dev`).
- `http://localhost:8788` — `wrangler pages dev` local emulator.

**No `*` wildcard origin** — T-04-08 mitigation. Cross-origin asset
substitution requires the attacker to land an exact-string match in
the allowlist; preview-deploy URLs are scoped via wildcard
subdomain only.

### Allowed methods — read-only

`GET` + `HEAD` only. No `PUT`/`POST`/`DELETE`/`PATCH`. T-04-06
mitigation: a leaked API token used by the browser-facing CORS surface
cannot mutate the bucket. Writes happen only via the GH Actions
`r2-sync.yml` workflow which uses the S3-compat endpoint (NOT the
custom domain) with the secret-bearing rclone client.

### Allowed headers — request-pre-conditional only

`Range`, `If-Match`, `If-None-Match`, `If-Modified-Since`,
`If-Unmodified-Since`. These cover the conditional-GET path needed by
the SW (Phase 4 plan 04-03 `@vite-pwa/astro` injectManifest cache-first
strategy for fonts + images, network-first for HTML, no-cache for
PDFs/videos — but conditional GETs still flow through the SW per
D-21). Notably absent: `Authorization`, `X-*` custom headers — the
bucket is fully public so no auth is sent from the browser.

### Exposed headers — caching + range-streaming

`Content-Length`, `Content-Range`, `Content-Type`, `ETag`,
`Last-Modified`. `Content-Range` exposes the byte-range responses
browsers issue when streaming a `<video>` element. `ETag` +
`Last-Modified` let the SW conditional-GET path work even when the
response is otherwise cross-origin.

### MaxAge — 24h preflight cache

`86400` seconds = 24 hours. Per CF docs the upper bound is 86400; we
take it. Cuts preflight chatter to negligible on a stable allowlist.

## Smoke verification (post-CORS-apply, pre-bulk-migration)

Operator captured this curl output at plan-execute time:

```
$ curl -sI -H "Origin: https://realufo.org" https://assets.realufo.org/
HTTP/2 404
access-control-allow-origin: https://realufo.org
```

The `HTTP/2 404` is expected — the bucket is empty so the root
listing is a miss. The `access-control-allow-origin` echo proves
CORS is wired correctly and the custom-domain bind resolves to the
bucket. Post-bulk-migration the smoke flips to `HTTP/2 200` on
sample PDF/video URLs (per `tests/r2-urls.spec.ts`).

## GitHub Actions secrets

| Secret | Used For | Status |
|--------|----------|--------|
| `CLOUDFLARE_API_TOKEN` | Wrangler bearer auth (CF Pages deploys, future zone-level operations) | Existing (Phase 2) |
| `CLOUDFLARE_ACCOUNT_ID` | Wrangler + rclone endpoint URL (`https://<account>.r2.cloudflarestorage.com`) | Existing (Phase 2) |
| `CLOUDFLARE_R2_ACCESS_KEY` | rclone S3-compat auth — `access_key_id` field in rclone config | NEW — added at plan-execute time |
| `CLOUDFLARE_R2_SECRET_KEY` | rclone S3-compat auth — `secret_access_key` field in rclone config | NEW — added at plan-execute time |

### Why both `CLOUDFLARE_API_TOKEN` AND `CLOUDFLARE_R2_ACCESS_KEY`/`SECRET_KEY`

These are TWO DIFFERENT auth schemes for TWO DIFFERENT R2 surfaces:

1. **`CLOUDFLARE_API_TOKEN`** is a Cloudflare-native bearer token used
   by `wrangler` (and any other CF API caller). Surface: the
   Cloudflare REST API at `https://api.cloudflare.com/client/v4/...`.
   Used for: project create/delete, bucket create, custom-domain
   bind, listing zones, listing buckets, applying CORS via
   `wrangler r2 bucket cors set`. **Not usable with rclone** — rclone
   speaks S3, not the CF REST API.
2. **`CLOUDFLARE_R2_ACCESS_KEY` + `CLOUDFLARE_R2_SECRET_KEY`** are
   S3-compatible credentials created via CF Dashboard → R2 → Manage
   R2 API Tokens. Surface: the S3-compat endpoint at
   `https://<account>.r2.cloudflarestorage.com`. Used for: rclone,
   `aws s3 sync`, the AWS SDK, any third-party S3 client. **Not
   usable with wrangler** — wrangler speaks the CF REST API.

`r2-sync.yml` uses rclone (the S3-compat path) because rclone gives
us idempotent checksum-based incremental sync out of the box. The
post-sync deploy trigger (if needed) would go through
`CLOUDFLARE_API_TOKEN` instead. Both secrets stay in the repo's GH
Actions secrets vault so a future migration to one or the other path
is a config change, not a credential rotation.

The R2 API token created for `CLOUDFLARE_R2_ACCESS_KEY`/`SECRET_KEY`
was scoped at creation time to "Object Read & Write" on bucket
`realufo` only (T-04-06 mitigation per 04-02-PLAN.md threat model).
Rotation procedure: revoke the token via Dashboard → R2 → Manage R2
API Tokens → Delete → re-create with the same scope → update both
GH secrets in a single Settings → Secrets and variables → Actions
edit (no in-flight gap because GH Actions reads at workflow-start,
not continuously).

## A3 decision — thumbnails stay local

**LOCKED 2026-05-27** per `04-CONTEXT.md` D-01 + `04-RESEARCH.md`
§Pitfall #7. The original D-01 wording said "Full migration of ALL
PDFs, videos, AND thumbnails to Cloudflare R2". Research surfaced a
conflict: Astro's `astro:assets` Image component only processes LOCAL
images (responsive srcset, format conversion, lazy-load hints). R2-
hosted thumbnails would skip Astro Image optimisation entirely —
mobile would download desktop-sized JPEGs, blowing PERF-04 budgets.

**Resolution:** thumbs stay local (tracked in git under per-archive
`<slug>/thumbs/` directories or equivalent legacy paths; small files,
already cheap in git). Only PDFs + videos migrate to R2. D-01 narrows
to "PDFs + videos only".

The `rewrite_to_r2()` helper enforces this at the function level: any
input ending in `.png`/`.jpg`/`.jpeg`/`.gif`/`.webp`/`.svg`/`.avif`/
`.bmp` (extension match, query-string and fragment stripped first) is
returned **as-is**. Image rows (CSV `Type=IMG`) where the
`PDF | Image Link` field is itself a `.png` URL stay pointed at the
original source URL — they never get rewritten to an R2 URL that
doesn't exist.

This affects:
- The 14 wargov rows with `Type=IMG` whose `PDF | Image Link` is
  `https://www.war.gov/.../fbi-photo-a*.png` — they remain pointed at
  the war.gov origin.
- All per-archive thumbnail paths (the `Modal Image` CSV column,
  separate from `PDF | Image Link`) — `normalize-csv.py` never
  rewrites this column at all; thumbs are read by Astro Image at
  build time.

## First-run bulk migration method (D-04)

Operator-triggered via `gh workflow run r2-sync.yml -f full_sync=true`
after this plan merges to main. The workflow's `full_sync` input path
skips diff detection and runs `rclone sync --checksum --progress`
against every tracked PDF + mp4 in the repo. Per 04-RESEARCH.md §4
this completes in ~5–10 min for the ~200 binaries at ~1.5 s each.

**Why rclone (S3-compat) and not `wrangler r2 object put` per-file:**
rclone gives us checksum-based idempotency for free — re-running the
same workflow is a no-op when the bucket is already in sync. Per-file
`wrangler` would have to re-implement that with a shell loop +
manual ETag comparison. rclone's `--checksum` flag costs negligible
Class A R2 operations (~200 ops × $0.0036 / 1000 = ~$0.0007 per sync,
quoted from 04-RESEARCH.md §5).

**Incremental sync trigger:** push to main with `paths-filter` on
`**/*.pdf` / `**/*.mp4` / `**/*.webm`. Subsequent commits that
rename/add binaries replay only the diff. `r2-sync.yml` has
`concurrency.cancel-in-progress: false` (T-04-07 mitigation — never
cancel an in-flight upload).

## Phase 4 + Phase 6 invariants honored

- **D-01 (refined per Pitfall #7):** PDFs + videos migrate to R2;
  thumbs stay local. `rewrite_to_r2()` enforces this at the function
  level via the `_IMAGE_EXTS` allowlist.
- **D-02:** Custom domain `assets.realufo.org` is the stable URL.
  Never reference `*.r2.dev` from cards/normalisers.
- **D-03:** GH Actions upload pipeline at `.github/workflows/r2-sync.yml`.
  Triggers on push to main with binary-paths filter + workflow_dispatch
  for full sync.
- **D-04:** First-run bulk migration via workflow_dispatch
  (`full_sync: true`). Subsequent runs incremental via rclone
  checksum diff.
- **D-05:** Single bucket `realufo`, prefix layout
  `pdfs/<slug>/`, `videos/<slug>/`. Avoids per-type CORS / lifecycle
  policy fragmentation.
- **D-06:** GH Releases tags `pdfs-v1` + `videos-v1` kept read-only as
  cold-storage backup. Cards do NOT reference them — `rewrite_to_r2()`
  emits R2 URLs exclusively.
- **D-24:** CORS scope per `r2-cors.json` — explicit allowlist of
  realufo.org + preview origins + localhost dev; GET+HEAD only.
- **CLAUDE.md §5.1 supersession:** the master spec said
  "GH Releases stays, R2 for >2 GB overflow only". Phase 4 supersedes
  this for PDFs + videos — R2 is the canonical CDN for those types;
  GH Releases is cold-storage backup only. Thumbnails per A3 stay
  local (neither R2 nor GH Releases).

## Operator note — what was done at plan-execute time

The orchestrator handled these manual steps before this agent started
Task 2:

1. `wrangler r2 bucket create realufo` → "Created bucket 'realufo'"
2. `wrangler r2 bucket cors set realufo --file ./r2-cors.json --force`
   (r2-cors.json was committed in advance at git sha `e9ff48c`)
3. Custom domain bind: Dashboard → R2 → realufo → Settings → Custom
   Domains → Connect Domain → `assets.realufo.org` → confirm.
   CF auto-created the proxied CNAME `assets` in the realufo.org zone.
4. R2 API token created via Dashboard → R2 → Manage R2 API Tokens →
   "Create API token" → "Object Read & Write" scope → bucket
   `realufo` only.
5. GH secrets added: `CLOUDFLARE_R2_ACCESS_KEY`,
   `CLOUDFLARE_R2_SECRET_KEY`. `CLOUDFLARE_API_TOKEN` +
   `CLOUDFLARE_ACCOUNT_ID` already present from Phase 2.
6. Smoke: `curl -sI -H "Origin: https://realufo.org" https://assets.realufo.org/`
   → `HTTP/2 404` + `access-control-allow-origin: https://realufo.org`
   (404 because bucket is empty — expected pre-bulk-migration).

## Future-phase hooks

- **Phase 4 close (plan 04-20)** flips the Lighthouse SOFT gate to
  HARD per D-40. If LCP / transfer budgets miss for any archive
  because R2 latency > local file serving, this doc gets a new
  `## Latency Findings` section.
- **Phase 5 (scrape automation, SCRP)** writes scraped binaries
  directly to R2 instead of committing to repo (D-deferred). When
  that lands, this doc gets a `## Scrape-to-R2 Write Path` section
  documenting the second writer (Workers cron → R2 direct put via
  S3 SDK using the same `CLOUDFLARE_R2_ACCESS_KEY`/`SECRET_KEY`).
- **Phase 6 (cutover, HOST-01)** — `realufo.org` apex flips from
  GH Pages anycast (`185.199.108-111.153`) to CF Pages. R2 is
  unaffected; `assets.realufo.org` continues to resolve at CF since
  the bucket already lives there. Only the page references shift.

## Locked-by

Phase 4 plan-phase + plan 04-02 (R2 setup) — execute-phase pass at
2026-05-27. Plan: `.planning/phases/04-full-migration-search-offline-performance/04-02-PLAN.md`.
Future amendments require a follow-up plan; do not hand-edit this doc
outside an `04-` phase or higher.
