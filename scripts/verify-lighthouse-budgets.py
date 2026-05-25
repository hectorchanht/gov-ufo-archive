#!/usr/bin/env python3
"""Parse Lighthouse-CI run output and emit WARN lines for any URL exceeding D-27 budgets.

D-27 budgets:
  - largest-contentful-paint <= 2500 ms
  - total-byte-weight        <= 512000 bytes (500 KB)

D-28 phase mode:
  - Phase 2 + Phase 3: SOFT — script ALWAYS exits 0 even on budget violations.
    Warnings appear in PR logs but do NOT block merge.
  - Phase 4 close: operator flips Plan 02-08's quality-gates.yml to invoke this
    with `--hard-fail`; only then does the script exit 1 on violations.

Plan 02-08 wires this into quality-gates.yml. The `lighthouse` job runs:

    sed "s|__PREVIEW_URL__|$PREVIEW_URL|g" .lighthouserc.cf.json > /tmp/lhci.json
    pnpm exec lhci autorun --config=/tmp/lhci.json || true   # soft per D-28
    python3 scripts/verify-lighthouse-budgets.py             # soft per D-28

LHCI 0.14 output schema (verified by 02-07 smoke test on 2026-05-25):
  .lighthouseci/lhr-<timestamp>.json        — per-URL Lighthouse Report JSON
                                              (top-level `finalUrl` + `audits.<id>.numericValue`)
  .lighthouseci/assertion-results.json      — array of {url, auditId, actual, expected, passed, level, ...}
                                              (one entry per (URL, audit) — primary parse path)
  .lighthouseci/lhr-<timestamp>.html        — human-readable HTML report (ignored by this parser)

This script prefers `assertion-results.json` (already filtered to budget audits
by `.lighthouserc.cf.json` assert.assertions) and falls back to globbing
`lhr-*.json` if assertion-results is absent.

NB: There is NO `manifest.json` in LHCI 0.14 — the plan's read_first block
references it from older LHCI docs. Schema confirmed empirically in the 02-07
smoke test before this script was written.

CLI:
    python3 scripts/verify-lighthouse-budgets.py                   # default soft mode
    python3 scripts/verify-lighthouse-budgets.py --lhci-dir <path> # override directory
    python3 scripts/verify-lighthouse-budgets.py --hard-fail       # Phase 4+ mode
    python3 scripts/verify-lighthouse-budgets.py --color           # ANSI red on WARN lines

Exit codes:
    0 — success OR soft-mode violations (D-28 default)
    1 — `--hard-fail` and at least one budget violation (Phase 4 close)
    2 — missing or unreadable .lighthouseci/ output (LHCI did not run)

Stdlib only — `argparse`, `json`, `pathlib`, `sys`. Matches the
`stdlib-only except curl_cffi` convention from CLAUDE.md §6.2 and the
style of `scripts/snapshot-urls.py` (PMS-01).

Refs: INF-08, D-26, D-27, D-28.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Iterable

# --- D-27 budgets -----------------------------------------------------------
LCP_BUDGET_MS = 2500
BYTE_WEIGHT_BUDGET_BYTES = 512000

# --- repo layout ------------------------------------------------------------
REPO = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_LHCI_DIR = REPO / ".lighthouseci"

# --- audit IDs (must match .lighthouserc.cf.json assert.assertions) ---------
AUDIT_LCP = "largest-contentful-paint"
AUDIT_BYTES = "total-byte-weight"

# --- ANSI colour codes (used only with --color) ------------------------------
ANSI_RED = "\x1b[31m"
ANSI_GREEN = "\x1b[32m"
ANSI_RESET = "\x1b[0m"


def _fmt(text: str, code: str, *, color: bool) -> str:
    return f"{code}{text}{ANSI_RESET}" if color else text


def _fmt_bytes(n: int | float) -> str:
    """Render a byte count as a human-readable KB string (no fractional precision needed)."""
    return f"{int(n) // 1024} KB"


def _load_assertion_results(lhci_dir: pathlib.Path) -> list[dict] | None:
    """Read .lighthouseci/assertion-results.json (primary parse path)."""
    path = lhci_dir / "assertion-results.json"
    if not path.is_file():
        return None
    try:
        with path.open() as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[error] could not parse {path}: {exc}", file=sys.stderr)
        return None
    if not isinstance(data, list):
        print(f"[error] {path} is not a JSON array (got {type(data).__name__})", file=sys.stderr)
        return None
    return data


def _load_lhr_files(lhci_dir: pathlib.Path) -> list[dict]:
    """Fallback parse path: glob lhr-*.json files (each is one URL's full report)."""
    reports: list[dict] = []
    for path in sorted(lhci_dir.glob("lhr-*.json")):
        try:
            with path.open() as handle:
                reports.append(json.load(handle))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[warn] skipping unreadable LHR file {path}: {exc}", file=sys.stderr)
    return reports


def _rows_from_assertion_results(records: Iterable[dict]) -> dict[str, dict[str, float]]:
    """Group assertion-results.json entries by URL → {audit_id: actual_value}."""
    by_url: dict[str, dict[str, float]] = {}
    for record in records:
        audit = record.get("auditId")
        if audit not in (AUDIT_LCP, AUDIT_BYTES):
            continue
        url = record.get("url", "<unknown>")
        actual = record.get("actual")
        if actual is None:
            continue
        by_url.setdefault(url, {})[audit] = float(actual)
    return by_url


def _rows_from_lhr_files(reports: Iterable[dict]) -> dict[str, dict[str, float]]:
    """Extract budget metrics from full LHR JSON dumps."""
    by_url: dict[str, dict[str, float]] = {}
    for lhr in reports:
        url = lhr.get("finalUrl") or lhr.get("requestedUrl") or "<unknown>"
        audits = lhr.get("audits", {})
        row: dict[str, float] = {}
        lcp = audits.get(AUDIT_LCP, {}).get("numericValue")
        if lcp is not None:
            row[AUDIT_LCP] = float(lcp)
        tbw = audits.get(AUDIT_BYTES, {}).get("numericValue")
        if tbw is not None:
            row[AUDIT_BYTES] = float(tbw)
        if row:
            by_url[url] = row
    return by_url


def _format_status_line(
    url: str,
    metrics: dict[str, float],
    *,
    color: bool,
) -> tuple[str, bool]:
    """Return (formatted_row, violated_any_budget)."""
    lcp_ms = metrics.get(AUDIT_LCP)
    tbw_bytes = metrics.get(AUDIT_BYTES)

    lcp_violates = lcp_ms is not None and lcp_ms > LCP_BUDGET_MS
    tbw_violates = tbw_bytes is not None and tbw_bytes > BYTE_WEIGHT_BUDGET_BYTES
    violates = lcp_violates or tbw_violates

    lcp_str = f"{int(lcp_ms)} ms" if lcp_ms is not None else "—"
    tbw_str = _fmt_bytes(tbw_bytes) if tbw_bytes is not None else "—"

    if violates:
        reasons = []
        if lcp_violates:
            reasons.append(f"LCP>{LCP_BUDGET_MS}ms")
        if tbw_violates:
            reasons.append(f"bytes>{BYTE_WEIGHT_BUDGET_BYTES // 1024}KB")
        status = _fmt(f"[WARN] {'/'.join(reasons)}", ANSI_RED, color=color)
    else:
        status = _fmt("[ok]", ANSI_GREEN, color=color)

    # 50-char URL column keeps the table readable for the 18 budget URLs without
    # truncating the realufo.pages.dev preview origin.
    row = f"  {url[:50]:<50}  {lcp_str:>10}  {tbw_str:>10}  {status}"
    return row, violates


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="verify-lighthouse-budgets.py",
        description=(
            "Parse Lighthouse-CI output and emit WARN lines for D-27 budget violations. "
            "Phase 2/3 mode is SOFT per D-28 — always exits 0 unless --hard-fail. "
            "See module docstring for full context."
        ),
    )
    parser.add_argument(
        "--lhci-dir",
        type=pathlib.Path,
        default=DEFAULT_LHCI_DIR,
        help=(
            "Directory containing LHCI output (default: .lighthouseci/ at repo root). "
            "Plan 02-08's CI job runs `lhci autorun` then this script in the same job step."
        ),
    )
    parser.add_argument(
        "--hard-fail",
        action="store_true",
        help=(
            "Exit 1 on any budget violation. Default off (Phase 2/3 soft mode per D-28). "
            "Phase 4 close flips this on once PERF-01 GEIPAN inline-JSON refactor lands."
        ),
    )
    parser.add_argument(
        "--color",
        action="store_true",
        help="Emit ANSI colour codes (red on WARN, green on ok).",
    )
    args = parser.parse_args()

    lhci_dir: pathlib.Path = args.lhci_dir

    if not lhci_dir.is_dir():
        print(
            f"[error] LHCI output directory not found: {lhci_dir} "
            f"(manifest / lhr files missing — did `lhci autorun` run?)",
            file=sys.stderr,
        )
        return 2

    # Prefer assertion-results.json (already filtered by .lighthouserc.cf.json
    # assert.assertions to exactly the two budget audits we care about).
    assertion_records = _load_assertion_results(lhci_dir)
    if assertion_records is not None:
        by_url = _rows_from_assertion_results(assertion_records)
        source = "assertion-results.json"
    else:
        # Fallback: glob lhr-*.json and pull budget metrics directly.
        reports = _load_lhr_files(lhci_dir)
        if not reports:
            print(
                f"[error] LHCI output directory contains no assertion-results.json "
                f"and no lhr-*.json reports: {lhci_dir}",
                file=sys.stderr,
            )
            return 2
        by_url = _rows_from_lhr_files(reports)
        source = "lhr-*.json (assertion-results.json absent)"

    if not by_url:
        print(
            f"[error] No budget audits ({AUDIT_LCP} / {AUDIT_BYTES}) found in "
            f"{lhci_dir} ({source}); check .lighthouserc.cf.json assert.assertions block.",
            file=sys.stderr,
        )
        return 2

    # --- print table ------------------------------------------------------
    print(f"Lighthouse budgets (D-27) — source: {source}")
    print(
        f"  {'URL':<50}  {'LCP':>10}  {'TRANSFER':>10}  STATUS  "
        f"(budgets: LCP <= {LCP_BUDGET_MS} ms, transfer <= {BYTE_WEIGHT_BUDGET_BYTES // 1024} KB)"
    )

    total = 0
    violators = 0
    for url in sorted(by_url):
        line, violated = _format_status_line(url, by_url[url], color=args.color)
        print(line)
        total += 1
        if violated:
            violators += 1

    ok = total - violators
    summary = (
        f"\n  {ok}/{total} URL(s) within budget; "
        f"{violators} URL(s) over budget."
    )
    print(summary)

    if violators == 0:
        return 0

    # Violators present.
    if args.hard_fail:
        print(
            "  [hard-fail] At least one URL exceeded budget — exiting non-zero "
            "(Phase 4 close mode per D-28).",
            file=sys.stderr,
        )
        return 1

    # Default Phase 2/3 soft mode per D-28: warn-only, never block merge.
    print(
        "  [soft-mode] Phase 2/3 soft per D-28: budget violations recorded above "
        "but exit code is 0. Re-run with --hard-fail at Phase 4 close once PERF-01 "
        "(GEIPAN inline-JSON refactor) lands."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
