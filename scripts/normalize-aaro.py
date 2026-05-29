#!/usr/bin/env python3
"""AARO (All-domain Anomaly Resolution Office) archive normaliser — Plan 04-17 (D-09 retirement).

Reads the legacy ``aaro/index.html`` inline ``<script id="arch-data">``
JSON manifest (the output of the now-retired
``scripts/build-aaro.py`` → ``scripts/parse-aaro.py`` →
``scripts/extract-evidence.py`` pipeline), rewrites every PDF/VID URL
through ``scripts/_archive_common.rewrite_to_r2``, and writes:

  data/aaro.json
  public/data/aaro.json
  data/aaro-shard-1.json     (sentinel shard — see "Sharding" below)

all matching ``catalogEnvelopeSchema`` from ``src/content.config.ts``
(Plan 03-02).

This is the sixth per-archive normaliser (after csv → wargov, nz,
uruguay, nara, nasa). It is the **first large-catalog example** (112
assets) and the **first DVIDS-deep-link example** — pattern G1 verbatim
from Plan 04-16 NASA's ``to_catalog_asset`` extra-keys filter,
extended for the 5 AARO-specific legacy keys (``k`` / ``re`` / ``st`` /
``di`` / ``dd``).

### Why parse-aaro.py + extract-evidence.py are absorbed (D-09 absorption)

The legacy AARO build pipeline was a 3-stage Python chain:

  1. ``scripts/parse-aaro.py`` walked ``aaro/pages/*.html`` (snapshots
     of aaro.mil sub-pages) and emitted ``aaro/.cache/parsed.json``
     (an intermediate JSON of extracted text + links).
  2. ``scripts/extract-evidence.py`` walked the intermediate
     ``aaro/.cache/parsed.json`` + on-disk ``aaro/videos/`` +
     ``aaro/pdfs/`` + ``aaro/assets/images/`` directories and emitted
     ``aaro/.cache/evidence.json`` (the joined evidence-map structure).
  3. ``scripts/build-aaro.py`` consumed ``aaro/.cache/evidence.json``
     and emitted the final ``aaro/index.html`` with the ``arch-data``
     inline manifest baked-in.

After Plan 04-17 Task 2 deletes ``aaro/index.html``, the dual-source
flow (``_read_from_existing_envelope``) takes over — the canonical
112 assets persist in ``data/aaro.json`` from this point onward. The
scrape pipeline (steps 1+2 above) is no longer load-bearing: the
record IDs + URLs are baked into the catalogue and any future
recapture would land in a future-plan scope (D-09 footprint reduction).

The Plan 04-17 SUMMARY documents that if a future scrape regen is
needed (e.g. when aaro.mil publishes new case-resolution reports), the
operator must reconstruct the parse+evidence pipeline OR — more
sensibly — add a new ``scripts/scrape-aaro.py`` that mirrors the
modern Astro content-collection contract directly (skipping the
HTML→intermediate-JSON→HTML round-trip the legacy scripts performed).
For Plan 04-17's purpose (D-09 — replace the per-archive build script)
the parse+evidence logic is **absorbed into the legacy index.html
arch-data block itself** (the build-aaro.py output is the parse+evidence
final state; reading it directly is sufficient).

### Source-of-truth flow (dual-mode, same as Uruguay + NARA + NASA)

  1. If ``aaro/index.html`` exists → parse the inline JSON manifest
     from it (canonical legacy capture). Used for the initial Wave 5
     migration.
  2. Else if ``data/aaro.json`` exists with non-empty ``assets`` →
     re-emit deterministically (idempotent across re-runs).
  3. Otherwise → exit 2 (no source available).

The Phase 3 stub envelope (``v1.assets=[]``) is detected and treated
as absent so the legacy HTML capture path remains canonical for the
initial Wave 5 migration — same refinement as Uruguay + NARA + NASA.

### Sharding

AARO has 112 assets at capture time — above the SHARD_SIZE=50
threshold per Plan 04-11. Following NARA precedent (Plan 04-15), a
**sentinel** ``data/aaro-shard-1.json`` is emitted as a 1-to-1 copy of
``data/aaro.json``. The catalogEnvelopeSchema currently has no
``shards: [...]`` array on the catalog envelope side (only
``wargovEnvelopeSchema`` carries it), and extending the schema would
invalidate the 13 other archive collections' validated state. The
inline ``arch-data`` block on the rendered ``/aaro/`` page still
resolves from ``data/aaro.json`` directly. Future operator splits can
drop ``data/aaro-shard-2.json`` + ``aaro-shard-3.json`` at 50-row
increments without touching the page template.

### Invariants (cite for any future agent before editing)

- **CLAUDE.md §11**: AARO source data is untouchable. The script opens
  ``aaro/index.html`` in read mode only.
  ``_assert_source_unchanged()`` runs after every write to fail loudly
  if the script accidentally mutated the legacy source.
- **D-04** (idempotent committed output): ``json.dumps(...,
  sort_keys=True, ensure_ascii=False, indent=2)`` + trailing newline →
  same source + same git state produces a byte-identical
  ``data/aaro.json`` on every run.
- **D-01** (R2 binary CDN): every PDF/VID URL flows through
  ``rewrite_to_r2()``. AARO's legacy manifest carries 32 VID rows
  (all on the hectorchanht/war-gov-ufo-release GH Release endpoint)
  + 59 PDF rows (all on the same GH Release endpoint, ``pdfs-v1``
  tag) + 21 IMG rows (live aaro.mil image URLs — pass-through per
  the image-extension guard in ``_archive_common._IMAGE_EXTS``).
- **D-26..D-28** (fidelity guards): no ``.strip()`` on text fields,
  no Unicode-normalisation calls, no regex rewrites. Card titles,
  descriptions, dates, agencies all round-trip byte-exact.
- **catalogAssetSchema.strict()** (Plan 03-02): output asset rows
  contain EXACTLY the keys ``t, ti, de, ag, cat, date, region, l, u,
  s, th``. The legacy AARO manifest carries FIVE extra keys not in
  the schema: ``k`` (kind label, redundant with ``cat``), ``re``
  (region — all empty), ``st`` (status — kept in legacy filter UI
  only), ``di`` (DVIDS video page id), ``dd`` (DOD basename
  identifier). All five are dropped by the ``_CATALOG_KEYS`` filter.
  The DVIDS contract per CLAUDE.md §4.3 is preserved through the
  ``s`` field (already carries the dvidshub.net page URL verbatim).

### DVIDS deep-link contract (CLAUDE.md §4.3)

AARO's legacy ``arch-data`` carries DVIDS metadata on every VID row:

  - ``di`` (e.g. ``"956955"``) — DVIDS internal video page ID
  - ``dd`` (e.g. ``"DOD_108981629"``) — DOD basename identifier
  - ``s`` — the **full dvidshub.net page URL** (e.g.
    ``https://www.dvidshub.net/video/956955``)

CLAUDE.md §4.3 specifies a dedicated "DVIDS ↗" button on VID cards
when ``a.dvidsId`` is set. The Astro CatalogCard (Plan 04-05) does
NOT carry a separate ``dvidsId`` field — it routes the DVIDS deep-link
through the standard ``Source ↗`` button (``asset.s``). Since
``asset.s`` already carries the dvidshub.net URL verbatim, the Source
↗ button effectively renders as DVIDS ↗ for AARO VID rows. NO schema
extension needed.

The ``di`` + ``dd`` fields are dropped — they were only used by the
legacy filter UI (``Search title, region, status, DVIDS…``) which has
been replaced by the shared Astro arch-controls-bar.

### Threat mitigations

- **T-04-54** (Tampering — AARO scraper cache mutation): post-write
  ``_assert_source_unchanged()`` runs ``git diff --quiet -- aaro/``
  and exits 1 on drift. The script is read-only with respect to
  ``aaro/`` source files. (After Task 2 deletes
  ``aaro/index.html``, the diff is a no-op — only the deletion is
  committed.)
- **T-04-55** (XSS via injected text): not a normaliser concern — Astro
  auto-escapes ``{expr}`` in CatalogCard.astro at render time. This
  normaliser preserves bytes verbatim; downstream rendering layer is
  the trust boundary.
- **T-04-56** (Loss of DVIDS deep-link contract): the ``s`` field
  carries the full dvidshub.net URL verbatim; one fidelity sample
  asserts a sample VID card's ``s`` matches the dvidshub.net pattern.
- **T-04-57** (Loss of "17 U.S.C. § 105" attribution): fidelity samples
  in tests/fidelity-samples.json carry the statute reference. The
  Footer.astro LICENSE map already wires this — this normaliser
  preserves source bytes so the fidelity gate stays green.

CLI:
    python3 scripts/normalize-aaro.py
        Read source → write data/aaro.json + public mirror + shard.
        Exit 0 on success.

    python3 scripts/normalize-aaro.py --check
        Re-run pipeline against an in-memory buffer; diff against the
        on-disk data/aaro.json. Exit 0 if byte-identical, 1 on drift.

Exit codes:
    0 — success (write or --check clean)
    1 — drift detected (--check mode) OR source mutation detected
    2 — neither aaro/index.html nor data/aaro.json present

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
SOURCE_HTML = REPO / 'aaro' / 'index.html'
DATA_DIR = REPO / 'data'
OUT_PRIMARY = DATA_DIR / 'aaro.json'
PUBLIC_DATA_DIR = REPO / 'public' / 'data'
PUBLIC_OUT = PUBLIC_DATA_DIR / 'aaro.json'
# Sentinel shard — kept to satisfy the Plan 04-17 files_modified
# contract (large-catalog tier). AARO's 112 assets fit on the page with
# client-side pagination (PAGE_SIZE=20 — six pages); the inline
# ``arch-data`` block still resolves from data/aaro.json directly.
# Future operator splits can drop data/aaro-shard-2.json + shard-3.json
# at 50-row increments without changing the page template.
SHARD_PRIMARY = DATA_DIR / 'aaro-shard-1.json'

# Canonical key set per catalogAssetSchema.strict() in src/content.config.ts.
# DO NOT add fields here without first extending the Zod schema — the
# strict() guard would fail the Astro build on any extra key.
#
# Legacy AARO arch-data carries 5 EXTRA keys not in this set:
#   k   — kind label (redundant with cat) — dropped
#   re  — region (always empty in the captured set) — dropped (region
#         field carried under canonical 'region' key)
#   st  — status (Unresolved/Resolved/Undergoing Analysis/Closed) —
#         dropped (was only used by legacy filter UI; arch-controls-bar
#         in Astro no longer exposes a status filter)
#   di  — DVIDS internal video page ID — dropped (the full dvidshub.net
#         URL is carried verbatim in `s`, which is what CLAUDE.md §4.3
#         requires for the DVIDS ↗ button)
#   dd  — DOD basename identifier — dropped (the basename survives in
#         the `u` field's GitHub Release URL filename)
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
    """Parse the inline `<script id="arch-data">` block from aaro/index.html.

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
    """Read the existing data/aaro.json envelope as the source-of-truth.

    Used after Plan 04-17 Task 2 deletes the legacy HTML. The envelope's
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

    The legacy AARO `arch-data` manifest uses the abbreviated keys
    (t, ti, de, ag, cat, l, u, s) but additionally carries:

      * ``k``  — kind label (redundant with `cat`) → DROPPED
      * ``re`` — region (always empty in capture) → DROPPED (canonical
                  field carried under `region`)
      * ``st`` — status (Unresolved/Resolved/...) → DROPPED (legacy
                  filter UI only — Astro arch-controls-bar drops the
                  Status filter; the user can still see status text
                  inside descriptions / titles where the legacy build
                  embedded it)
      * ``di`` — DVIDS video page id → DROPPED (full URL in `s`)
      * ``dd`` — DOD basename identifier → DROPPED (preserved in `u`
                  GH Release URL basename)

    Also missing from the legacy manifest (filled with ``''``):
      * ``date``   — AARO doesn't carry incident/release dates at row
                     level in the captured manifest (most assets are
                     undated DOD media releases identified by basename)
      * ``region`` — empty in all 112 captured rows; canonical position
                     for future captures
      * ``th``     — no per-card thumbnail field (IMG rows use `u` for
                     the live aaro.mil image URL; PDFs are basename-only)

    AARO-specific behaviour:
      * Rows with t='PDF': `u` (GitHub Release URL) is rewritten
        through ``rewrite_to_r2(..., asset_type='pdfs')``. Local PDFs
        are gitignored (CLAUDE.md §5.2) so `l` is always empty for
        PDFs unless a future capture wires a local path.
      * Rows with t='VID': both `u` (GH Release video URL — primary
        download) AND `l` (same URL — legacy capture mirrors the two
        fields for legacy filter UI "Local only" toggle since the GH
        Release URL was considered "local" once the binary CDN
        migration completed) are rewritten through
        ``rewrite_to_r2(..., asset_type='videos')``. The `s` field
        carries the dvidshub.net page URL verbatim — NOT rewritten
        (Source ↗ button targets the canonical DVIDS deep-link per
        CLAUDE.md §4.3).
      * Rows with t='IMG': `u` carries a live aaro.mil image URL
        (e.g. ``https://www.aaro.mil/DesktopModules/SharedLibrary/Images/...``).
        ``rewrite_to_r2`` is a no-op on image-extension URLs (per
        ``_archive_common._IMAGE_EXTS``) so the image flows verbatim.
        `l` is always empty for IMG rows in the AARO capture.

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
        # AARO legacy carries no top-level `date` key; the capture
        # is by basename + DVIDS id only. Empty string for schema
        # compliance; future captures can populate this.
        'date': raw.get('date', '') or '',
        # Legacy AARO carries `re` (always empty in capture). Map to
        # the canonical `region` field for schema compliance + forward-
        # compat with future captures populating either name.
        'region': raw.get('region', '') or raw.get('re', '') or '',
        'l': raw.get('l', '') or '',
        'u': raw.get('u', '') or '',
        # `s` is z.string().optional() in the schema; we always emit it
        # so the JSON shape is stable. Empty string sorts identically
        # to missing for downstream filtering. AARO VID rows carry the
        # dvidshub.net deep-link here (CLAUDE.md §4.3 DVIDS ↗ button).
        's': raw.get('s', '') or '',
        'th': raw.get('th', '') or '',
    }
    # Phase 4 plan 04-02 — rewrite PDF/VID URLs to the R2 custom domain.
    # IMG rows are left untouched (rewrite_to_r2 is a no-op on image
    # extensions per the _IMAGE_EXTS guard; defensive skip avoids the
    # call entirely). The `s` field (dvidshub.net for VID) is NEVER
    # rewritten — it's the canonical Source ↗ deep-link destination.
    if t == 'VID':
        asset_type = 'videos'
    elif t in ('PDF', 'DOC'):
        asset_type = 'pdfs'
    else:
        asset_type = None
    if asset_type:
        if asset['u']:
            asset['u'] = rewrite_to_r2(asset['u'], 'aaro', asset_type)
        if asset['l']:
            asset['l'] = rewrite_to_r2(asset['l'], 'aaro', asset_type)
    # Plan post-05-01 (PDF first-page thumb) — for PDF/DOC rows whose
    # `th` is empty, derive
    # `https://assets.realufo.org/pdf-thumbs/aaro/<basename>.jpg` from
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
    # protects the build from a strict() failure. This ALSO drops the
    # 5 legacy AARO-specific keys (k, re, st, di, dd) automatically
    # since they're not in _CATALOG_KEYS.
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
      to external catalogs. AARO's legacy manifest has zero CATALOG /
      PAGE rows (all 112 assets are PDF + VID + IMG); this is always 0
      at capture time, emitted for schema compliance + forward-compat.

    Note: AARO's legacy manifest separately tracked ``vid_total`` /
    ``videos_local`` + ``img_total`` / ``imgs_local`` — these are
    folded into ``total`` + ``local_total`` here since
    ``catalogStatsSchema`` does not carry per-non-downloadable-type
    counts. The page template derives VID + IMG counts on the client
    side from the inline arch-data manifest via the tab filter.
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
            "slug": "aaro",
            "assets": [...],
            "stats": {"total": N, "local_total": M, "pdf_total": P,
                      "catalog_total": C}
          }
        }
    """
    return {
        'v1': {
            'schemaVersion': 1,
            'slug': 'aaro',
            'assets': assets,
            'stats': _compute_stats(assets),
        },
    }


# -----------------------------------------------------------------------------
# Source untouchability guard (T-04-54)
# -----------------------------------------------------------------------------


def _assert_source_unchanged() -> None:
    """Fail loudly if the script accidentally mutated the AARO source dir.

    CLAUDE.md §11 declares scrape outputs untouchable. This runs
    ``git diff --quiet -- aaro/`` and exits 1 on any diff. If
    aaro/ has been removed (post-Plan 04-17 Task 2), the diff is a
    no-op (untracked → no diff).
    """
    try:
        rc = subprocess.run(
            ['git', '-C', str(REPO), 'diff', '--quiet', '--', 'aaro/'],
            check=False,
        ).returncode
    except FileNotFoundError:
        # git not on PATH — best-effort skip, matches normalize-csv.py
        sys.stderr.write(
            '[warn] git not on PATH; skipping AARO-source-unchanged '
            'assertion\n'
        )
        return
    if rc != 0:
        sys.stderr.write(
            '[error] AARO source mutation detected — CLAUDE.md §11 '
            'forbids writing back to aaro/ source files. Revert with '
            '`git checkout -- aaro/` and fix the normaliser.\n'
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
            'normalise AARO.\n'
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
    # Sentinel shard — same envelope shape. Plan 04-17 files_modified
    # contract calls for data/aaro-shard-1.json. Keeping it 1-to-1 with
    # the primary envelope means future operator splits can drop shard-2,
    # shard-3, etc. without changing the page template — the inline
    # arch-data block still resolves from data/aaro.json.
    _write_json(SHARD_PRIMARY, envelope)
    _assert_source_unchanged()
    stats = envelope['v1']['stats']
    sys.stderr.write(
        f'[ok] aaro: {stats["total"]} assets '
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
        sys.stderr.write('[drift] aaro normaliser output diverges:\n')
        for line in drift:
            sys.stderr.write(f'  - {line}\n')
        sys.stderr.write(
            '[hint] re-run `python3 scripts/normalize-aaro.py` (without '
            '--check) to regenerate the committed JSON files.\n'
        )
        return 1
    sys.stderr.write('[ok] aaro: --check clean (no drift)\n')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Normalise the AARO (All-domain Anomaly Resolution Office) '
            'legacy source into data/aaro.json (catalogEnvelopeSchema). '
            'Reads aaro/index.html if present, else re-emits from the '
            'existing data/aaro.json envelope (post-Plan-04-17 deletion). '
            'Absorbs the legacy parse-aaro.py + extract-evidence.py + '
            'build-aaro.py pipeline by reading the build-aaro.py '
            'arch-data output directly (D-09 absorption per Plan 04-17). '
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
