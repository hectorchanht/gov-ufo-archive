#!/usr/bin/env python3
"""NARA UAP Records archive normaliser — Plan 04-15 (D-09 retirement).

Reads the legacy ``nara/index.html`` inline ``<script id="arch-data">``
JSON manifest, rewrites every PDF/VID URL through
``scripts/_archive_common.rewrite_to_r2``, and writes:

  data/nara.json
  public/data/nara.json
  data/nara-shard-1.json    (sentinel shard — see "Sharding" below)

all matching ``catalogEnvelopeSchema`` from
``src/content.config.ts`` (Plan 03-02).

This is the third per-archive normaliser (D-08 Wave 2 — medium catalog
tier; NARA carries 73 assets at capture time — PDF + PAGE + CATALOG
mix). The pattern is verbatim from ``scripts/normalize-uruguay.py``
(Plan 04-06) with these deltas:

  1. ``CATALOG`` and ``PAGE`` rows: ``rewrite_to_r2`` is a no-op
     (no local download file — ``l`` is empty, ``u`` carries the
     catalog.archives.gov / archives.gov deep-link verbatim).
  2. ``PDF`` rows: ``u`` (GitHub Release URL today) is rewritten to the
     R2 custom-domain (``https://assets.realufo.org/pdfs/nara/...``).
  3. Sharding: emits an additional ``data/nara-shard-1.json`` file that
     contains the same envelope (sentinel — kept for the files_modified
     contract and forward-compat with a future >50-card shard split).
     The page-level pagination handler reads from the in-DOM cards
     directly (PAGE_SIZE=20) so the shard file is informational at this
     stage.

### Source-of-truth flow (dual-mode, same as Uruguay)

Phase 4 plan 04-15 ALSO deletes the legacy ``nara/index.html`` (D-09 —
per-archive Python retirement). The normaliser is dual-mode:

  1. If ``nara/index.html`` exists → parse the inline JSON manifest
     from it (canonical legacy capture). Used for the initial Wave 5
     migration.
  2. Else if ``data/nara.json`` exists with non-empty ``assets`` →
     re-emit deterministically (idempotent across re-runs).
  3. Otherwise → exit 2 (no source available).

The Phase 3 stub envelope (``v1.assets=[]``) is detected and treated as
absent so the legacy HTML capture path remains canonical for the
initial Wave 5 migration — same refinement as the Uruguay normaliser.

### Invariants (cite for any future agent before editing)

- **CLAUDE.md §11**: NARA source data is untouchable. The script opens
  ``nara/index.html`` in read mode only.
  ``_assert_source_unchanged()`` runs after every write to fail loudly
  if the script accidentally mutated the legacy source.
- **D-04** (idempotent committed output): ``json.dumps(...,
  sort_keys=True, ensure_ascii=False, indent=2)`` + trailing newline →
  same source + same git state produces a byte-identical
  ``data/nara.json`` on every run.
- **D-01** (R2 binary CDN): every PDF/VID URL flows through
  ``rewrite_to_r2()``. NARA's legacy manifest carries 53 PDFs + 11
  CATALOG + 9 PAGE rows (no videos as of capture date) — the PDF
  ``u`` URLs are GitHub Release URLs that get rewritten to R2; CATALOG
  + PAGE rows have empty ``l`` and an external ``u`` URL that stays
  verbatim.
- **D-26..D-28** (fidelity guards): no ``.strip()`` on text fields,
  no Unicode-normalisation calls, no regex rewrites. Card titles,
  descriptions, dates, agencies all round-trip byte-exact.
- **catalogAssetSchema.strict()** (Plan 03-02): output asset rows
  contain EXACTLY the keys ``t, ti, de, ag, cat, date, region, l, u,
  s, th``. The legacy NARA manifest omits ``region`` and ``th`` — we
  fill them as ``''``. ``s`` (Source URL) is preserved verbatim from
  the legacy manifest.

### Threat mitigations

- **T-04-48** (Tampering — NARA Catalog cache mutation): post-write
  ``_assert_source_unchanged()`` runs ``git diff --quiet -- nara/``
  and exits 1 on drift. The script is read-only with respect to
  ``nara/`` source files.
- **T-04-49** (XSS via injected text): not a normaliser concern — Astro
  auto-escapes ``{expr}`` in CatalogCard.astro at render time. This
  normaliser preserves bytes verbatim; downstream rendering layer is
  the trust boundary.
- **T-04-50** (Loss of "17 U.S.C. § 105" attribution): fidelity samples
  in tests/fidelity-samples.json carry the statute reference. The
  Footer.astro LICENSE map already wires this — this normaliser
  preserves source bytes so the fidelity gate stays green.

CLI:
    python3 scripts/normalize-nara.py
        Read source → write data/nara.json + public mirror + shard.
        Exit 0 on success.

    python3 scripts/normalize-nara.py --check
        Re-run pipeline against an in-memory buffer; diff against the
        on-disk data/nara.json. Exit 0 if byte-identical, 1 on drift.

Exit codes:
    0 — success (write or --check clean)
    1 — drift detected (--check mode) OR source mutation detected
    2 — neither nara/index.html nor data/nara.json present

Stdlib only — argparse, json, re, subprocess, sys, pathlib. Imports
``rewrite_to_r2`` from ``_archive_common`` (Plan 04-02).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Local-import: scripts/_archive_common.py exposes the R2 URL rewrite helper
# used by every Phase 4 per-archive normaliser. Inserting scripts/ at
# sys.path[0] keeps this script runnable from any cwd without requiring
# package install (stdlib-only convention per CLAUDE.md §6.2).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _archive_common import pdf_thumb_url, rewrite_to_r2  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
SOURCE_HTML = REPO / 'nara' / 'index.html'
DATA_DIR = REPO / 'data'
OUT_PRIMARY = DATA_DIR / 'nara.json'
PUBLIC_DATA_DIR = REPO / 'public' / 'data'
PUBLIC_OUT = PUBLIC_DATA_DIR / 'nara.json'
# Sentinel shard — kept to satisfy the Plan 04-15 files_modified contract
# (medium-catalog tier). NARA's 73 assets fit on the page without
# pagination, but future captures may grow; the shard file gives Plan
# 04-19 Pagefind a deterministic per-archive shard manifest path.
SHARD_PRIMARY = DATA_DIR / 'nara-shard-1.json'

# Canonical key set per catalogAssetSchema.strict() in src/content.config.ts.
# DO NOT add fields here without first extending the Zod schema — the
# strict() guard would fail the Astro build on any extra key.
_CATALOG_KEYS: tuple[str, ...] = (
    't', 'ti', 'de', 'ag', 'cat', 'date', 'region', 'l', 'u', 's', 'th',
)

# Inline-manifest extraction regex. The legacy build-<slug>.py scripts
# emit a single `<script id="arch-data" type="application/json">{...}</script>`
# block (CLAUDE.md §6.2). Non-greedy match between the open/close tags
# tolerates surrounding whitespace + the type attribute.
_SCRIPT_RE = re.compile(
    r'<script\s+id="arch-data"\s+type="application/json">(?P<body>.*?)</script>',
    re.DOTALL,
)


# -----------------------------------------------------------------------------
# Source ingest (read-only)
# -----------------------------------------------------------------------------


def _read_from_legacy_html() -> dict[str, Any] | None:
    """Parse the inline `<script id="arch-data">` block from nara/index.html.

    Returns the decoded JSON dict (with `assets` + `stats` keys) on
    success; ``None`` if the legacy HTML is absent. Raises on malformed
    JSON — fail loudly rather than silently emit empty data.
    """
    if not SOURCE_HTML.exists():
        return None
    text = SOURCE_HTML.read_text(encoding='utf-8')
    match = _SCRIPT_RE.search(text)
    if not match:
        sys.stderr.write(
            f'[error] {SOURCE_HTML.relative_to(REPO)} found but contains '
            'no <script id="arch-data"> block. Check the legacy build '
            'script output before re-running.\n'
        )
        sys.exit(1)
    body = match.group('body')
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        sys.stderr.write(
            f'[error] {SOURCE_HTML.relative_to(REPO)} <script id="arch-data"> '
            f'body is not valid JSON: {exc}\n'
        )
        sys.exit(1)
    sys.stderr.write(
        f'[info] read {len(data.get("assets", []))} assets from legacy '
        f'{SOURCE_HTML.relative_to(REPO)}\n'
    )
    return data


def _read_from_existing_envelope() -> dict[str, Any] | None:
    """Read the existing data/nara.json envelope as the source-of-truth.

    Used after Plan 04-15 Task 2 deletes the legacy HTML. The envelope's
    ``assets`` array is the canonical record from that point onward.
    Returns ``{assets, stats}`` (matching the legacy HTML shape) on
    success; ``None`` if the envelope is missing OR carries no assets
    (the stub envelope emitted by Phase 3 had assets=[] — treat as
    absent so the legacy HTML path remains canonical for the initial
    Wave 5 migration capture). Refinement inherited from Plan 04-06.
    """
    if not OUT_PRIMARY.exists():
        return None
    text = OUT_PRIMARY.read_text(encoding='utf-8')
    try:
        envelope = json.loads(text)
    except json.JSONDecodeError as exc:
        sys.stderr.write(
            f'[error] {OUT_PRIMARY.relative_to(REPO)} is not valid JSON: {exc}\n'
        )
        sys.exit(1)
    v1 = envelope.get('v1', {})
    assets = v1.get('assets', []) or []
    if not assets:
        # Stub envelope from Phase 3 scaffolding — treat as absent so
        # the legacy HTML path captures the real catalogue rows.
        sys.stderr.write(
            f'[info] {OUT_PRIMARY.relative_to(REPO)} present but empty '
            '— falling through to legacy HTML capture\n'
        )
        return None
    sys.stderr.write(
        f'[info] re-emit mode: read {len(assets)} assets '
        f'from existing {OUT_PRIMARY.relative_to(REPO)}\n'
    )
    return {
        'assets': assets,
        'stats': v1.get('stats', {}),
    }


# -----------------------------------------------------------------------------
# Asset mapping (raw row → catalogAssetSchema)
# -----------------------------------------------------------------------------


def to_catalog_asset(raw: dict[str, Any]) -> dict[str, str]:
    """Map one source row to a catalogAssetSchema.strict()-valid dict.

    The legacy `arch-data` manifest already uses the abbreviated keys
    (t, ti, de, ag, cat, date, region, l, u, s, th) — this mirrors the
    `scripts/templates/archive.py` schema that build-<slug>.py scripts
    were emitting. We re-key explicitly to:

      * filter out any unexpected keys the legacy manifest might carry
        (strict() would fail the build otherwise);
      * fill missing optional keys with their schema defaults
        (empty string for everything except `s` which is `optional`);
      * apply ``rewrite_to_r2`` to PDF/VID URLs in `u` and `l`.

    NARA-specific behaviour:
      * Rows with t='PAGE' or t='CATALOG' carry an external gateway URL
        in `u` (catalog.archives.gov, archives.gov, vault.fbi.gov, …) —
        ``rewrite_to_r2`` is NOT applied (no R2-hosted asset; the URL
        IS the destination). `l` is always empty for these rows.
      * Rows with t='PDF' carry a GitHub Release URL in `u` and an
        empty `l` (legacy capture stripped local paths once PDFs moved
        to GitHub Releases). The GH Release URL is rewritten to the R2
        custom-domain per D-01 (the basename survives — fileonly URL
        rewriting).

    Image extensions are preserved verbatim by ``rewrite_to_r2`` per
    D-01 refinement + Pitfall #7 (thumbnails stay local for Astro Image).
    """
    t = (raw.get('t', '') or '').strip()
    asset: dict[str, str] = {
        't': t,
        'ti': raw.get('ti', '') or '',
        'de': raw.get('de', '') or '',
        'ag': raw.get('ag', '') or '',
        'cat': raw.get('cat', '') or '',
        'date': raw.get('date', '') or '',
        'region': raw.get('region', '') or '',
        'l': raw.get('l', '') or '',
        'u': raw.get('u', '') or '',
        # `s` is z.string().optional() in the schema; we always emit it
        # so the JSON shape is stable. Empty string sorts identically
        # to missing for downstream filtering.
        's': raw.get('s', '') or '',
        'th': raw.get('th', '') or '',
    }
    # Phase 4 plan 04-02 — rewrite PDF/VID URLs to the R2 custom domain.
    # CASE / CATALOG / PAGE / IMG / AUDIO rows are left untouched (no R2
    # prefix would make sense — they point at external catalog pages).
    if t == 'VID':
        asset_type = 'videos'
    elif t in ('PDF', 'DOC'):
        asset_type = 'pdfs'
    else:
        asset_type = None
    if asset_type:
        if asset['u']:
            asset['u'] = rewrite_to_r2(asset['u'], 'nara', asset_type)
        if asset['l']:
            asset['l'] = rewrite_to_r2(asset['l'], 'nara', asset_type)
    # Plan post-05-01 (PDF first-page thumb) — for PDF/DOC rows whose
    # `th` is empty, derive
    # `https://assets.realufo.org/pdf-thumbs/nara/<basename>.jpg` from
    # the R2-rewritten `u`. CatalogCard.astro reads `asset.th` directly
    # and its <img> onerror falls back to `data-fallback` (the PDF URL).
    # The matching JPG is rendered + uploaded to R2 by
    # `scripts/build-pdf-thumbs.py`. Additive — non-empty `th` preserved.
    if t in ('PDF', 'DOC') and not (asset.get('th') or '').strip():
        derived = pdf_thumb_url(asset.get('u') or '')
        if derived:
            asset['th'] = derived
    # Final defensive guard — ensure ONLY the strict-schema keys leak
    # out. If any future maintainer adds a key to the dict literal
    # above without extending catalogAssetSchema, this filter still
    # protects the build from a strict() failure.
    return {k: asset[k] for k in _CATALOG_KEYS}


# -----------------------------------------------------------------------------
# Envelope construction
# -----------------------------------------------------------------------------


def _compute_stats(assets: list[dict[str, str]]) -> dict[str, int]:
    """Compute the four catalogStatsSchema counts.

    - total: number of assets
    - local_total: assets with non-empty `l` (locally available)
    - pdf_total: assets with t in {PDF, DOC}
    - catalog_total: assets with t in {CATALOG, PAGE} — gateway entries
      to external catalogs (per CLAUDE.md §4.3 + the NARA legacy
      manifest which uses PAGE for institutional gateway pages and
      CATALOG for NARA Catalog deep-links).
    """
    total = len(assets)
    local_total = sum(1 for a in assets if a['l'])
    pdf_total = sum(1 for a in assets if a['t'] in ('PDF', 'DOC'))
    # NARA uses both CATALOG (NARA Catalog deep-links) and PAGE
    # (federal-agency gateway HTML pages). Both are non-downloadable
    # gateway entries — group them in catalog_total to match
    # catalogStatsSchema (which has no `pages_total` field).
    catalog_total = sum(1 for a in assets if a['t'] in ('CATALOG', 'PAGE'))
    return {
        'total': total,
        'local_total': local_total,
        'pdf_total': pdf_total,
        'catalog_total': catalog_total,
    }


def _build_envelope(assets: list[dict[str, str]]) -> dict[str, Any]:
    """Construct the v1 envelope per catalogEnvelopeSchema.

    Shape:
        {
          "v1": {
            "schemaVersion": 1,
            "slug": "nara",
            "assets": [...],
            "stats": {"total": N, "local_total": M, "pdf_total": P,
                      "catalog_total": C}
          }
        }
    """
    return {
        'v1': {
            'schemaVersion': 1,
            'slug': 'nara',
            'assets': assets,
            'stats': _compute_stats(assets),
        },
    }


# -----------------------------------------------------------------------------
# Source untouchability guard (T-04-48)
# -----------------------------------------------------------------------------


def _assert_source_unchanged() -> None:
    """Fail loudly if the script accidentally mutated the NARA source dir.

    CLAUDE.md §11 declares scrape outputs untouchable. This runs
    ``git diff --quiet -- nara/`` and exits 1 on any diff. If
    nara/ has been removed (post-Plan 04-15 Task 2), the diff is a
    no-op (untracked → no diff).
    """
    try:
        rc = subprocess.run(
            ['git', '-C', str(REPO), 'diff', '--quiet', '--', 'nara/'],
            check=False,
        ).returncode
    except FileNotFoundError:
        # git not on PATH — best-effort skip, matches normalize-csv.py
        sys.stderr.write(
            '[warn] git not on PATH; skipping NARA-source-unchanged '
            'assertion\n'
        )
        return
    if rc != 0:
        sys.stderr.write(
            '[error] NARA source mutation detected — CLAUDE.md §11 '
            'forbids writing back to nara/ source files. Revert with '
            '`git checkout -- nara/` and fix the normaliser.\n'
        )
        sys.exit(1)


# -----------------------------------------------------------------------------
# JSON write (deterministic per D-04)
# -----------------------------------------------------------------------------


def _serialise(data: Any) -> str:
    """Deterministic JSON serialisation per D-04 idempotency requirement.

    Same convention as scripts/normalize-csv.py:
      - sort_keys=True
      - ensure_ascii=False (preserve Unicode bytes verbatim per D-26..D-28)
      - indent=2
      - trailing newline (POSIX convention)
    """
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n'


def _write_json(path: Path, data: Any) -> None:
    """Write `data` to `path` as deterministic JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_serialise(data), encoding='utf-8')


# -----------------------------------------------------------------------------
# Normalisation pipeline (pure — for --check reuse)
# -----------------------------------------------------------------------------


def _normalise() -> dict[str, Any]:
    """Run the full normalisation pipeline and return the envelope dict."""
    source = _read_from_legacy_html()
    if source is None:
        source = _read_from_existing_envelope()
    if source is None:
        sys.stderr.write(
            f'[error] neither {SOURCE_HTML.relative_to(REPO)} nor a '
            f'populated {OUT_PRIMARY.relative_to(REPO)} exists. Cannot '
            'normalise NARA.\n'
        )
        sys.exit(2)
    raw_assets = source.get('assets', []) or []
    assets = [to_catalog_asset(r) for r in raw_assets]
    return _build_envelope(assets)


# -----------------------------------------------------------------------------
# CLI entrypoints
# -----------------------------------------------------------------------------


def _write_mode() -> int:
    """Default mode: normalise source → write JSON files (+ sentinel shard)."""
    envelope = _normalise()
    DATA_DIR.mkdir(exist_ok=True)
    _write_json(OUT_PRIMARY, envelope)
    _write_json(PUBLIC_OUT, envelope)
    # Sentinel shard — same envelope shape. Plan 04-15 files_modified
    # contract calls for data/nara-shard-1.json. Keeping it 1-to-1 with
    # the primary envelope means future operator splits can drop shard-2,
    # shard-3, etc. without changing the page template — the inline
    # arch-data block still resolves from data/nara.json.
    _write_json(SHARD_PRIMARY, envelope)
    _assert_source_unchanged()
    stats = envelope['v1']['stats']
    sys.stderr.write(
        f'[ok] nara: {stats["total"]} assets '
        f'(local={stats["local_total"]} pdf={stats["pdf_total"]} '
        f'catalog={stats["catalog_total"]}) written to '
        f'{OUT_PRIMARY.relative_to(REPO)} + '
        f'{PUBLIC_OUT.relative_to(REPO)} + '
        f'{SHARD_PRIMARY.relative_to(REPO)}\n'
    )
    return 0


def _check_mode() -> int:
    """--check mode: normalise to memory + diff against on-disk file.

    Exit 0 if byte-identical, 1 on drift. Mirrors normalize-csv.py's
    --check semantics.
    """
    envelope = _normalise()
    expected = _serialise(envelope)
    drift: list[str] = []
    for path in (OUT_PRIMARY, PUBLIC_OUT, SHARD_PRIMARY):
        if not path.exists():
            drift.append(f'{path.relative_to(REPO)} missing on disk')
            continue
        actual = path.read_text(encoding='utf-8')
        if actual != expected:
            drift.append(f'{path.relative_to(REPO)} drift')
    if drift:
        sys.stderr.write('[drift] nara normaliser output diverges:\n')
        for line in drift:
            sys.stderr.write(f'  - {line}\n')
        sys.stderr.write(
            '[hint] re-run `python3 scripts/normalize-nara.py` (without '
            '--check) to regenerate the committed JSON file.\n'
        )
        return 1
    sys.stderr.write('[ok] nara: --check clean (no drift)\n')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Normalise the NARA UAP Records legacy source into '
            'data/nara.json (catalogEnvelopeSchema). Reads '
            'nara/index.html if present, else re-emits from the '
            'existing data/nara.json envelope (post-Plan-04-15 '
            'deletion). Idempotent + deterministic per D-04.'
        ),
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help=(
            'Run the pipeline and compare to on-disk JSON without '
            'writing. Exit 1 on drift.'
        ),
    )
    args = parser.parse_args(argv)
    if args.check:
        return _check_mode()
    return _write_mode()


if __name__ == '__main__':
    sys.exit(main())
