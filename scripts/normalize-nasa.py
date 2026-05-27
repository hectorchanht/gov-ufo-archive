#!/usr/bin/env python3
"""NASA UAP Independent Study Team archive normaliser — Plan 04-16 (D-09 retirement).

Reads the legacy ``nasa/index.html`` inline ``<script id="arch-data">``
JSON manifest, rewrites every PDF/VID URL through
``scripts/_archive_common.rewrite_to_r2``, and writes:

  data/nasa.json
  public/data/nasa.json

both matching ``catalogEnvelopeSchema`` from
``src/content.config.ts`` (Plan 03-02).

This is the fifth per-archive normaliser (after csv → wargov, nz,
uruguay, nara). The pattern is verbatim from
``scripts/normalize-nara.py`` (Plan 04-15) with these NASA-specific
deltas:

  1. NASA has 18 assets at capture time (small-catalog tier — well
     under the SHARD_SIZE=50 threshold). No sharding emitted; the
     primary envelope carries all rows.
  2. ``VID`` rows: ``rewrite_to_r2`` IS invoked with
     ``asset_type='videos'`` — but the legacy NASA manifest holds
     YouTube watch URLs (``https://www.youtube.com/watch?v=...`` or
     ``https://youtu.be/...``) which are not basename-stable assets we
     own. The helper strips the path and returns
     ``https://assets.realufo.org/videos/nasa/<basename>``, which is
     wrong for YouTube. For this reason, the normaliser SKIPS the
     rewrite when the URL host is youtube.com / youtu.be — these are
     third-party stream sources that stay verbatim.
  3. ``IMG`` rows: ``rewrite_to_r2`` is a no-op per the image-extension
     guard in ``_archive_common.rewrite_to_r2`` (which returns the
     input untouched for ``.png/.jpg/.jpeg/.gif/.webp/.svg`` URLs so
     Astro Image can process them locally per D-01 refinement +
     Pitfall #7).
  4. Legacy NASA manifest carries extra keys not in
     ``catalogAssetSchema``:
       - ``embed`` (YouTube embed URL on VID rows)
     These keys are dropped — strict() in the Zod schema would fail
     the build otherwise. The Lightbox already opens videos via the
     ``u`` URL (which falls through to YouTube), so no UX regression.
  5. Legacy stats counts ``vid_total`` + ``img_total`` separately —
     ``catalogStatsSchema`` (Plan 03-02) does not. NASA has zero
     CATALOG rows so ``catalog_total = 0``; VID + IMG rows count
     toward ``total`` and (when ``l`` is set) ``local_total``.

### Source-of-truth flow (dual-mode, same as Uruguay + NARA)

Phase 4 plan 04-16 ALSO deletes the legacy ``nasa/index.html`` (D-09 —
per-archive Python retirement). The normaliser is dual-mode:

  1. If ``nasa/index.html`` exists → parse the inline JSON manifest
     from it (canonical legacy capture). Used for the initial Wave 5
     migration.
  2. Else if ``data/nasa.json`` exists with non-empty ``assets`` →
     re-emit deterministically (idempotent across re-runs).
  3. Otherwise → exit 2 (no source available).

The Phase 3 stub envelope (``v1.assets=[]``) is detected and treated as
absent so the legacy HTML capture path remains canonical for the
initial Wave 5 migration — same refinement as Uruguay + NARA.

### Invariants (cite for any future agent before editing)

- **CLAUDE.md §11**: NASA source data is untouchable. The script opens
  ``nasa/index.html`` in read mode only.
  ``_assert_source_unchanged()`` runs after every write to fail loudly
  if the script accidentally mutated the legacy source.
- **D-04** (idempotent committed output): ``json.dumps(...,
  sort_keys=True, ensure_ascii=False, indent=2)`` + trailing newline →
  same source + same git state produces a byte-identical
  ``data/nasa.json`` on every run.
- **D-01** (R2 binary CDN): every PDF URL flows through
  ``rewrite_to_r2()``. NASA's legacy manifest carries 11 PDFs (mostly
  on the hectorchanht/war-gov-ufo-release GH Release endpoint already)
  + 5 VID rows (YouTube — pass-through) + 2 IMG rows (local repo paths
  — pass-through).
- **D-26..D-28** (fidelity guards): no ``.strip()`` on text fields,
  no Unicode-normalisation calls, no regex rewrites. Card titles,
  descriptions, dates, agencies all round-trip byte-exact.
- **catalogAssetSchema.strict()** (Plan 03-02): output asset rows
  contain EXACTLY the keys ``t, ti, de, ag, cat, date, region, l, u,
  s, th``. The legacy NASA manifest omits ``region`` + ``th`` (fill
  with ``''``) AND carries an extra ``embed`` key on VID rows (drop).

### Threat mitigations

- **T-04-51** (Tampering — NASA source mutation): post-write
  ``_assert_source_unchanged()`` runs ``git diff --quiet -- nasa/``
  and exits 1 on drift. The script is read-only with respect to
  ``nasa/`` source files.
- **T-04-52** (XSS via injected text): not a normaliser concern — Astro
  auto-escapes ``{expr}`` in CatalogCard.astro at render time. This
  normaliser preserves bytes verbatim; downstream rendering layer is
  the trust boundary.
- **T-04-53** (Loss of "17 U.S.C. § 105" attribution): fidelity samples
  in tests/fidelity-samples.json carry the statute reference. The
  Footer.astro LICENSE map already wires this — this normaliser
  preserves source bytes so the fidelity gate stays green.

CLI:
    python3 scripts/normalize-nasa.py
        Read source → write data/nasa.json + public mirror.
        Exit 0 on success.

    python3 scripts/normalize-nasa.py --check
        Re-run pipeline against an in-memory buffer; diff against the
        on-disk data/nasa.json. Exit 0 if byte-identical, 1 on drift.

Exit codes:
    0 — success (write or --check clean)
    1 — drift detected (--check mode) OR source mutation detected
    2 — neither nasa/index.html nor data/nasa.json present

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
SOURCE_HTML = REPO / 'nasa' / 'index.html'
DATA_DIR = REPO / 'data'
OUT_PRIMARY = DATA_DIR / 'nasa.json'
PUBLIC_DATA_DIR = REPO / 'public' / 'data'
PUBLIC_OUT = PUBLIC_DATA_DIR / 'nasa.json'

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

# YouTube hosts — the legacy NASA manifest's VID rows point at these
# third-party streams. ``rewrite_to_r2`` would mangle them into
# ``https://assets.realufo.org/videos/nasa/watch?v=...`` (basename of the
# YouTube watch URL is the ``v`` query string fragment after basename
# strip). Detect these hosts and skip the rewrite so the URL flows
# through to the lightbox / new-tab handler verbatim.
_YT_HOSTS: tuple[str, ...] = ('youtube.com', 'youtu.be', 'www.youtube.com')


# -----------------------------------------------------------------------------
# Source ingest (read-only)
# -----------------------------------------------------------------------------


def _read_from_legacy_html() -> dict[str, Any] | None:
    """Parse the inline `<script id="arch-data">` block from nasa/index.html.

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
    """Read the existing data/nasa.json envelope as the source-of-truth.

    Used after Plan 04-16 Task 2 deletes the legacy HTML. The envelope's
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


def _is_youtube_url(url: str) -> bool:
    """Return True if ``url`` host matches a known YouTube stream host.

    Cheap substring match is sufficient — the catalog only ever holds
    well-formed http(s) URLs, never URL-encoded or relative paths.
    """
    if not url:
        return False
    lower = url.lower()
    for host in _YT_HOSTS:
        if f'//{host}/' in lower or f'//{host}' == lower[: len(host) + 2]:
            return True
    return False


def to_catalog_asset(raw: dict[str, Any]) -> dict[str, str]:
    """Map one source row to a catalogAssetSchema.strict()-valid dict.

    The legacy NASA `arch-data` manifest uses the abbreviated keys
    (t, ti, de, ag, cat, date, l, u, s) but additionally carries:

      * ``embed`` on VID rows (YouTube embed URL) — DROPPED.

    Also missing from the legacy manifest (filled with ``''``):

      * ``region`` (NASA doesn't carry geo metadata at row level)
      * ``th`` (no per-card thumbnail field — IMG rows use `l` for the
        local image path).

    NASA-specific behaviour:
      * Rows with t='PDF': ``u`` (GitHub Release URL OR direct NASA URL)
        is rewritten through ``rewrite_to_r2(..., asset_type='pdfs')``.
        Local PDFs are gitignored (CLAUDE.md §5.2) so ``l`` is always
        empty for PDFs unless a future capture wires a local path.
      * Rows with t='VID': YouTube watch/embed URLs — skip
        ``rewrite_to_r2`` entirely (would mangle the URL into an
        R2 path against an asset we don't own). The CatalogCard's Open
        button forwards these through the lightbox, which falls back
        to a new-tab open for YouTube origins.
      * Rows with t='IMG': ``l`` carries a local repo-relative path
        (``assets/images/...``). ``rewrite_to_r2`` is a no-op on
        image-extension URLs (per ``_archive_common._IMAGE_EXTS``) so
        Astro Image can process them locally. The legacy manifest's
        IMG rows omit the ``s`` key — fill with ``''``.

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
    # NASA VID rows are YouTube watch URLs — skip the rewrite for those
    # since they are third-party streams we do not host.
    if t == 'VID':
        # VID rows in the NASA manifest are exclusively YouTube — skip
        # ``rewrite_to_r2`` entirely. If a future scrape captures a
        # locally-hosted MP4, swap this branch back to
        # asset_type='videos'.
        if not _is_youtube_url(asset['u']):
            if asset['u']:
                asset['u'] = rewrite_to_r2(asset['u'], 'nasa', 'videos')
            if asset['l']:
                asset['l'] = rewrite_to_r2(asset['l'], 'nasa', 'videos')
    elif t in ('PDF', 'DOC'):
        if asset['u']:
            asset['u'] = rewrite_to_r2(asset['u'], 'nasa', 'pdfs')
        if asset['l']:
            asset['l'] = rewrite_to_r2(asset['l'], 'nasa', 'pdfs')
    # IMG (and any other type) — rewrite_to_r2 already image-guards via
    # _IMAGE_EXTS, but we skip the call entirely so the helper is only
    # invoked for downloadable asset types. IMG rows pass verbatim so
    # Astro Image can process local `assets/images/*` paths.
    # Final defensive guard — ensure ONLY the strict-schema keys leak
    # out. If any future maintainer adds a key to the dict literal
    # above without extending catalogAssetSchema, this filter still
    # protects the build from a strict() failure. This ALSO drops the
    # legacy `embed` key on VID rows automatically since it's not in
    # _CATALOG_KEYS.
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
      to external catalogs. NASA's legacy manifest has zero CATALOG /
      PAGE rows (all assets are PDF + VID + IMG) so this is always 0
      at capture time; emitted for schema compliance + forward-compat.

    Note: NASA's legacy manifest separately tracked ``vid_total`` +
    ``img_total`` — these are folded into ``total`` here since
    ``catalogStatsSchema`` does not carry per-non-downloadable-type
    counts. The page template can derive VID + IMG counts on the
    client side from the inline arch-data manifest if needed.
    """
    total = len(assets)
    local_total = sum(1 for a in assets if a['l'])
    pdf_total = sum(1 for a in assets if a['t'] in ('PDF', 'DOC'))
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
            "slug": "nasa",
            "assets": [...],
            "stats": {"total": N, "local_total": M, "pdf_total": P,
                      "catalog_total": C}
          }
        }
    """
    return {
        'v1': {
            'schemaVersion': 1,
            'slug': 'nasa',
            'assets': assets,
            'stats': _compute_stats(assets),
        },
    }


# -----------------------------------------------------------------------------
# Source untouchability guard (T-04-51)
# -----------------------------------------------------------------------------


def _assert_source_unchanged() -> None:
    """Fail loudly if the script accidentally mutated the NASA source dir.

    CLAUDE.md §11 declares scrape outputs untouchable. This runs
    ``git diff --quiet -- nasa/`` and exits 1 on any diff. If
    nasa/ has been removed (post-Plan 04-16 Task 2), the diff is a
    no-op (untracked → no diff).
    """
    try:
        rc = subprocess.run(
            ['git', '-C', str(REPO), 'diff', '--quiet', '--', 'nasa/'],
            check=False,
        ).returncode
    except FileNotFoundError:
        # git not on PATH — best-effort skip, matches normalize-csv.py
        sys.stderr.write(
            '[warn] git not on PATH; skipping NASA-source-unchanged '
            'assertion\n'
        )
        return
    if rc != 0:
        sys.stderr.write(
            '[error] NASA source mutation detected — CLAUDE.md §11 '
            'forbids writing back to nasa/ source files. Revert with '
            '`git checkout -- nasa/` and fix the normaliser.\n'
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
            'normalise NASA.\n'
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
        f'[ok] nasa: {stats["total"]} assets '
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
    for path in (OUT_PRIMARY, PUBLIC_OUT):
        if not path.exists():
            drift.append(f'{path.relative_to(REPO)} missing on disk')
            continue
        actual = path.read_text(encoding='utf-8')
        if actual != expected:
            drift.append(f'{path.relative_to(REPO)} drift')
    if drift:
        sys.stderr.write('[drift] nasa normaliser output diverges:\n')
        for line in drift:
            sys.stderr.write(f'  - {line}\n')
        sys.stderr.write(
            '[hint] re-run `python3 scripts/normalize-nasa.py` (without '
            '--check) to regenerate the committed JSON file.\n'
        )
        return 1
    sys.stderr.write('[ok] nasa: --check clean (no drift)\n')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Normalise the NASA UAP Independent Study Team legacy source '
            'into data/nasa.json (catalogEnvelopeSchema). Reads '
            'nasa/index.html if present, else re-emits from the '
            'existing data/nasa.json envelope (post-Plan-04-16 '
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
