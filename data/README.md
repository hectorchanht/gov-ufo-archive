# `data/` — content-collection JSON for realufo.org

This directory holds the materialised input to Astro's Content Collection
loaders. Each `data/<slug>.json` corresponds to one of the 15 archives
listed in `CLAUDE.md §2`. The schema authority lives in
[`../src/content.config.ts`](../src/content.config.ts) — read it for field
names and types. This README documents the **envelope shape**, the
**writer responsibility** for each file, and the **fidelity guard** every
writer must honour.

## Envelope shape

Each file is a JSON object using the Astro 5 `file()` loader's
entries-object form. Top-level keys are entry IDs; values are the
schema-validated payload:

```json
{
  "v1": {
    "schemaVersion": 1,
    "slug": "<archive-slug>",
    "assets": [],
    "stats": { "total": 0, "local_total": 0, "pdf_total": 0, "catalog_total": 0 }
  }
}
```

For `data/wargov.json` the payload follows the **CSV-keyed** variant
(`rows[]` keyed by `uap-release001.csv` header columns verbatim) — see
`src/content.config.ts` → `wargovEnvelopeSchema`. Plan 03-03 produces this
file; it is intentionally absent in Phase 3 Plan 03-02.

Entry IDs are user-defined. Phase 3 uses a single `"v1"` per archive; future
schema migrations can append `"v2"`, `"v3"`, … and the loader will surface
each as a distinct content-collection entry.

## Writer responsibility

| File | Writer | Phase | Trigger |
| --- | --- | --- | --- |
| `data/wargov.json` | `scripts/normalize-csv.py` | 03-03 | `pnpm prebuild` reads `uap-release001.csv` + `uap-data.csv` |
| `data/aaro.json`, `nasa.json`, `nara.json`, `geipan.json`, `uk.json`, `brazil.json`, `chile.json`, `argentina.json`, `canada.json`, `italy.json`, `nz.json`, `peru.json`, `spain.json`, `uruguay.json` | Phase 4 SSG-06 per-archive normaliser → Phase 5 SCRP-01 cron-automated | 4 / 5 | Workers cron + GH Actions hybrid (research/STACK.md) |

Phase 3 commits the 14 non-wargov files as **schema-valid empty skeletons**
so Astro's `file()` loader can round-trip them without error. Phase 4 SSG-06
will replace the empty `assets: []` with real entries.

## Fidelity guard (CLAUDE.md §9; D-26..D-28; PITFALLS.md #6)

Verbatim official text fields — `ti`, `de`, `Title`, `Description Blurb`,
`Release Date`, `Incident Date`, `Incident Location`, and every other prose
field — **MUST NOT be mutated** by any normaliser. That includes:

- No smart-quote rewriting (`"` → `"`, `'` → `'`).
- No em-dash / en-dash auto-conversion.
- No HTML-entity decoding (e.g. `&amp;` → `&`) unless the upstream source
  guarantees the entity is encoding artefact rather than literal content.
- No whitespace normalisation beyond leading/trailing strip on outer fields.
- No accent stripping (`é` → `e`, `ñ` → `n`).
- No zero-width-character removal.

The schema at `src/content.config.ts` deliberately uses **no Zod
`transform()` or `preprocess()`** on text fields for the same reason. If a
normaliser needs to rewrite text, it must be discussed first and gated
behind a Phase 4+ decision record.

## Idempotency

Re-running any writer with identical inputs MUST produce a **byte-identical
output file**. Concretely:

- Use deterministic JSON serialisation. Python: `json.dumps(..., sort_keys=
  True, ensure_ascii=False, indent=2)` + trailing newline.
- No timestamps anywhere in the envelope.
- No random IDs, run identifiers, or build-host metadata.
- Stable sort of `assets[]` / `rows[]` by a documented key (e.g. release
  date then title).

Idempotency lets `pnpm prebuild` run on every CI build without producing a
spurious diff, and lets reviewers `git diff` two builds and see real data
changes — not formatter churn.

## Build-time validation

Astro's Content Collection loader runs the Zod schema on every entry at
build time. Schema-incompatible rows fail the build loudly (`ZodError` →
Astro propagation per D-03). This is the project's main defence against:

- CSV-header drift in `uap-release001.csv` (column rename, new column).
- Scrape-output drift in per-archive `.cache/` snapshots.
- Hand-edits to `data/*.json` that break the contract.

Do not soften the schema to make a bad row pass. Fix the row.
