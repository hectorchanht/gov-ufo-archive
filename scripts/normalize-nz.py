#!/usr/bin/env python3
"""NZ Defence Force archive normaliser — Plan 04-05 (D-09 retirement).

Reads the legacy `nz/index.html` inline `<script id="arch-data">` JSON
manifest, rewrites every PDF/VID URL through
``scripts/_archive_common.rewrite_to_r2``, and writes:

  data/nz.json
  public/data/nz.json

both matching ``catalogEnvelopeSchema`` from
``src/content.config.ts`` (Plan 03-02).

This is the FIRST per-archive normaliser (D-08 Wave 1 — smallest static
archive in the 14-catalog set). The same pattern will be cloned for
plans 04-06..04-18 (one per remaining catalog archive). Anything novel
that emerges here lives in ``scripts/_archive_common.py`` rather than
this file so the downstream 13 normalisers can reuse it.

### Source-of-truth flow

Phase 4 plan 04-05 ALSO deletes the legacy ``nz/index.html`` (D-09 —
per-archive Python retirement). The normaliser is dual-mode:

  1. If ``nz/index.html`` exists → parse the inline JSON manifest from
     it (canonical legacy capture). Use this path for the initial
     Wave 3 migration.
  2. Else if ``data/nz.json`` exists → read the existing envelope's
     ``assets`` array as the source-of-truth (re-emit deterministically
     so idempotency is preserved across re-runs).
  3. Otherwise → exit 2 (no source available).

Mode (2) means re-running the normaliser AFTER ``nz/index.html`` is
deleted in Plan 04-05 Task 3 still produces a byte-identical
``data/nz.json`` — `pnpm prebuild` stays green even on a fresh clone
that never had the legacy HTML. Future scrape automation (Phase 5)
will replace the parse with an HTTP fetch + DOM extraction.

### Invariants (cite for any future agent before editing)

- **CLAUDE.md §11**: NZ source data is untouchable. The script opens
  ``nz/index.html`` in read mode only. ``_assert_source_unchanged()``
  runs after every write to fail loudly if the script accidentally
  mutated the legacy source.
- **D-04** (idempotent committed output): ``json.dumps(...,
  sort_keys=True, ensure_ascii=False, indent=2)`` + trailing newline →
  same source + same git state produces a byte-identical
  ``data/nz.json`` on every run.
- **D-01** (R2 binary CDN): every PDF/VID URL flows through
  ``rewrite_to_r2()``. Image URLs (thumbnails) are preserved verbatim
  per Pitfall #7 (Astro Image processes LOCAL files only). NZ has no
  thumbnails today; the helper is still called for completeness.
- **D-26..D-28** (fidelity guards): no ``.strip()`` on text fields,
  no Unicode-normalisation calls, no regex rewrites. Card titles,
  descriptions, dates, agencies all round-trip byte-exact.
- **catalogAssetSchema.strict()** (Plan 03-02): output asset rows
  contain EXACTLY the keys ``t, ti, de, ag, cat, date, region, l, u,
  s, th``. Unknown keys would fail Zod validation at build time.

### Threat mitigations

- **T-04-19** (NZ scraper output tampering): post-write
  ``_assert_source_unchanged()`` runs ``git diff --quiet -- nz/`` and
  exits 1 on drift. The CSV/HTML/json sources are never written.
- **T-04-21** (XSS via injected fields): not a normaliser concern —
  Astro auto-escapes ``{expr}`` in CatalogCard.astro at render time.
  This normaliser preserves bytes verbatim; downstream rendering
  layer is the trust boundary.

CLI:
    python3 scripts/normalize-nz.py
        Read source → write data/nz.json + public mirror. Exit 0 on
        success.

    python3 scripts/normalize-nz.py --check
        Re-run pipeline against an in-memory buffer; diff against the
        on-disk data/nz.json. Exit 0 if byte-identical, 1 on drift.

Exit codes:
    0 — success (write or --check clean)
    1 — drift detected (--check mode) OR source mutation detected
    2 — neither nz/index.html nor data/nz.json present

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
from _archive_common import rewrite_to_r2  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
SOURCE_HTML = REPO / 'nz' / 'index.html'
DATA_DIR = REPO / 'data'
OUT_PRIMARY = DATA_DIR / 'nz.json'
PUBLIC_DATA_DIR = REPO / 'public' / 'data'
PUBLIC_OUT = PUBLIC_DATA_DIR / 'nz.json'

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
    """Parse the inline `<script id="arch-data">` block from nz/index.html.

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
    """Read the existing data/nz.json envelope as the source-of-truth.

    Used after Plan 04-05 Task 3 deletes the legacy HTML. The envelope's
    ``assets`` array is the canonical record from that point onward.
    Returns ``{assets, stats}`` (matching the legacy HTML shape) on
    success; ``None`` if the envelope is missing.
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
    sys.stderr.write(
        f'[info] re-emit mode: read {len(v1.get("assets", []))} assets '
        f'from existing {OUT_PRIMARY.relative_to(REPO)}\n'
    )
    return {
        'assets': v1.get('assets', []),
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
    # `u` is the canonical download URL; `l` is the local repo-relative
    # path (or, in NZ's legacy manifest, a duplicate GitHub release URL).
    # Both flow through the same helper so PDF + VID rows get rewritten
    # consistently. CASE / CATALOG / PAGE / IMG / AUDIO rows are left
    # untouched (no R2 prefix would make sense — they point at external
    # catalog pages).
    if t == 'VID':
        asset_type = 'videos'
    elif t in ('PDF', 'DOC'):
        asset_type = 'pdfs'
    else:
        asset_type = None
    if asset_type:
        if asset['u']:
            asset['u'] = rewrite_to_r2(asset['u'], 'nz', asset_type)
        if asset['l']:
            asset['l'] = rewrite_to_r2(asset['l'], 'nz', asset_type)
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
    - catalog_total: assets with t in {CATALOG} — gateway entries to
      external catalogs (per CLAUDE.md §4.3 + the NZ legacy manifest
      which uses CATALOG for institutional gateway pages).
    """
    total = len(assets)
    local_total = sum(1 for a in assets if a['l'])
    pdf_total = sum(1 for a in assets if a['t'] in ('PDF', 'DOC'))
    catalog_total = sum(1 for a in assets if a['t'] == 'CATALOG')
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
            "slug": "nz",
            "assets": [...],
            "stats": {"total": N, "local_total": M, "pdf_total": P,
                      "catalog_total": C}
          }
        }
    """
    return {
        'v1': {
            'schemaVersion': 1,
            'slug': 'nz',
            'assets': assets,
            'stats': _compute_stats(assets),
        },
    }


# -----------------------------------------------------------------------------
# Source untouchability guard (T-04-19)
# -----------------------------------------------------------------------------


def _assert_source_unchanged() -> None:
    """Fail loudly if the script accidentally mutated the NZ source dir.

    CLAUDE.md §11 declares scrape outputs untouchable. This runs
    ``git diff --quiet -- nz/`` and exits 1 on any diff. If nz/ has
    been removed (post-Plan 04-05 Task 3), the diff is a no-op
    (untracked → no diff).
    """
    try:
        rc = subprocess.run(
            ['git', '-C', str(REPO), 'diff', '--quiet', '--', 'nz/'],
            check=False,
        ).returncode
    except FileNotFoundError:
        # git not on PATH — best-effort skip, matches normalize-csv.py
        sys.stderr.write(
            '[warn] git not on PATH; skipping NZ-source-unchanged assertion\n'
        )
        return
    if rc != 0:
        sys.stderr.write(
            '[error] NZ source mutation detected — CLAUDE.md §11 forbids '
            'writing back to nz/ source files. Revert with '
            '`git checkout -- nz/` and fix the normaliser.\n'
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
            f'[error] neither {SOURCE_HTML.relative_to(REPO)} nor '
            f'{OUT_PRIMARY.relative_to(REPO)} exists. Cannot normalise NZ.\n'
        )
        sys.exit(2)
    raw_assets = source.get('assets', []) or []
    assets = [to_catalog_asset(r) for r in raw_assets]
    return _build_envelope(assets)


# -----------------------------------------------------------------------------
# CLI entrypoints
# -----------------------------------------------------------------------------


def _write_mode() -> int:
    """Default mode: normalise source → write JSON files."""
    envelope = _normalise()
    DATA_DIR.mkdir(exist_ok=True)
    _write_json(OUT_PRIMARY, envelope)
    _write_json(PUBLIC_OUT, envelope)
    _assert_source_unchanged()
    stats = envelope['v1']['stats']
    sys.stderr.write(
        f'[ok] nz: {stats["total"]} assets '
        f'(local={stats["local_total"]} pdf={stats["pdf_total"]} '
        f'catalog={stats["catalog_total"]}) written to '
        f'{OUT_PRIMARY.relative_to(REPO)} + '
        f'{PUBLIC_OUT.relative_to(REPO)}\n'
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
    if not OUT_PRIMARY.exists():
        drift.append(f'{OUT_PRIMARY.relative_to(REPO)} missing on disk')
    else:
        actual = OUT_PRIMARY.read_text(encoding='utf-8')
        if actual != expected:
            drift.append(f'{OUT_PRIMARY.relative_to(REPO)} drift')
    if not PUBLIC_OUT.exists():
        drift.append(f'{PUBLIC_OUT.relative_to(REPO)} missing on disk')
    else:
        actual = PUBLIC_OUT.read_text(encoding='utf-8')
        if actual != expected:
            drift.append(f'{PUBLIC_OUT.relative_to(REPO)} drift')
    if drift:
        sys.stderr.write('[drift] nz normaliser output diverges:\n')
        for line in drift:
            sys.stderr.write(f'  - {line}\n')
        sys.stderr.write(
            '[hint] re-run `python3 scripts/normalize-nz.py` (without '
            '--check) to regenerate the committed JSON file.\n'
        )
        return 1
    sys.stderr.write('[ok] nz: --check clean (no drift)\n')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Normalise the NZ Defence Force legacy source into '
            'data/nz.json (catalogEnvelopeSchema). Reads '
            'nz/index.html if present, else re-emits from the existing '
            'data/nz.json envelope (post-Plan-04-05 deletion). '
            'Idempotent + deterministic per D-04.'
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
