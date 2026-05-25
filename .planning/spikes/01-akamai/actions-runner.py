#!/usr/bin/env python3
"""Akamai Egress Spike — GitHub Actions / local runner probe lane.

Plan: .planning/phases/01-pre-migration-safety/01-03-PLAN.md (PMS-03).
Decision target: .planning/decisions/akamai-spike.md (D-12 — first ADR).
Companion: .planning/spikes/01-akamai/worker.ts (Cloudflare Worker lane).

Measures the *baseline* GitHub-Actions-runner egress stance vs Akamai
(war.gov, aaro.mil) so .planning/decisions/akamai-spike.md can apply the
D-11 threshold (Workers viable iff success rate ≥ 95% AND ≥ Actions success).

PER PLAN: stdlib only. Uses urllib.request — NOT requests, NOT curl_cffi.
The whole point of the Actions lane is to measure the *plain* runner.
The curl_cffi Chrome-TLS-spoof lane is the Phase 5 hybrid fallback that
SCRP-02 will design *only if* this baseline is insufficient.

Usage:
    # Sanity check — one fetch per target, no sleep
    python3 .planning/spikes/01-akamai/actions-runner.py --dry-run

    # Full 1-hour spike (100 fetches × 5 sources, parallel per-source)
    python3 .planning/spikes/01-akamai/actions-runner.py --duration 3600 --fetches-per-source 100

Outputs:
    .planning/spikes/01-akamai/results.json — appended under "actions_lane"
    (file is the destination Task 3 reads from to compute the per-source verdict)
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as _dt
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROBE_FILE = HERE / "probe-sources.json"
RESULTS_FILE = HERE / "results.json"

# UA contract — the User-Agent string is loaded from probe-sources.json at
# runtime (single source of truth shared with worker.ts). The literal string
# from .planning/codebase/CONCERNS.md, restated here for grep-discoverability:
#   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
#   "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

AKAMAI_COOKIE_NEEDLES = ("_abck=", "bm_sc=", "AKAM_SC=")
PARDON_NEEDLE = "Pardon Our Interruption"
DENIED_NEEDLE = "Access Denied"

# Locks results.json writes — ThreadPoolExecutor may race otherwise.
_results_lock = threading.Lock()


def _load_probe_sources() -> dict[str, Any]:
    if not PROBE_FILE.exists():
        sys.exit(f"FATAL: {PROBE_FILE} missing — Task 1 incomplete.")
    return json.loads(PROBE_FILE.read_text(encoding="utf-8"))


def _probe_once(target_url: str, user_agent: str, timeout: float = 30.0) -> dict[str, Any]:
    """Issue one GET, capture Akamai-signature fields. No redirects followed."""
    started = time.monotonic()
    iso_ts = _dt.datetime.now(_dt.timezone.utc).isoformat()
    req = urllib.request.Request(
        target_url,
        method="GET",
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    # No-redirect opener — Akamai often redirects to a challenge URL, which is
    # itself a 200; following hides the block.
    opener = urllib.request.build_opener(_NoRedirectHandler())

    body_bytes: bytes = b""
    body_total_len = 0
    http_status = 0
    server_hdr: str | None = None
    set_cookie_hdr: str = ""
    err_msg: str | None = None

    try:
        with opener.open(req, timeout=timeout) as resp:
            http_status = resp.status
            server_hdr = resp.headers.get("Server")
            set_cookie_hdr = resp.headers.get("Set-Cookie", "") or ""
            # Read up to first 2 KB for fingerprint (memory-safe even if source
            # hands us a huge HTML body during a block-page rate spike).
            body_bytes = resp.read(2048)
            # Drain the rest just for length count, discard payload.
            chunk = resp.read(4096)
            body_total_len = len(body_bytes) + len(chunk)
            while chunk:
                chunk = resp.read(8192)
                body_total_len += len(chunk)
    except urllib.error.HTTPError as e:
        http_status = e.code
        server_hdr = e.headers.get("Server") if e.headers else None
        set_cookie_hdr = (e.headers.get("Set-Cookie", "") if e.headers else "") or ""
        try:
            body_bytes = e.read(2048) or b""
            body_total_len = len(body_bytes)
        except Exception:  # noqa: BLE001 — best-effort fingerprint
            body_total_len = 0
        err_msg = f"HTTPError {e.code}"
    except urllib.error.URLError as e:
        err_msg = f"URLError: {e.reason}"
    except (TimeoutError, ConnectionError) as e:
        err_msg = f"{type(e).__name__}: {e}"
    except Exception as e:  # noqa: BLE001 — captures stdlib quirks across versions
        err_msg = f"{type(e).__name__}: {e}"

    body_snippet = body_bytes.decode("utf-8", errors="replace")
    cookie_hits = [n for n in AKAMAI_COOKIE_NEEDLES if n in set_cookie_hdr]
    latency_ms = int((time.monotonic() - started) * 1000)
    return {
        "lane": "actions",
        "target_url": target_url,
        "iso_timestamp": iso_ts,
        "http_status": http_status,
        "body_length_bytes": body_total_len,
        "latency_ms": latency_ms,
        "server_header": server_hdr,
        "akamai_cookie_present": bool(cookie_hits),
        "akamai_cookie_names": cookie_hits,
        "body_fingerprint_pardon_our_interruption": PARDON_NEEDLE in body_snippet,
        "body_fingerprint_access_denied": DENIED_NEEDLE in body_snippet,
        "error": err_msg,
    }


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Suppress urllib's default redirect-following so we observe the 3xx itself."""

    def http_error_302(self, req, fp, code, msg, headers):  # noqa: ARG002, D401
        return fp

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302


def _append_row(row: dict[str, Any]) -> None:
    with _results_lock:
        if RESULTS_FILE.exists():
            data = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
        else:
            data = {"worker_lane": [], "actions_lane": []}
        data.setdefault("actions_lane", []).append(row)
        RESULTS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _drive_one_source(
    target_url: str,
    user_agent: str,
    fetches_per_source: int,
    spacing_seconds: float,
    dry_run: bool,
) -> None:
    for i in range(fetches_per_source):
        row = _probe_once(target_url, user_agent)
        _append_row(row)
        print(
            f"[{row['iso_timestamp']}] {target_url} "
            f"status={row['http_status']} bytes={row['body_length_bytes']} "
            f"akamai_cookie={row['akamai_cookie_present']} server={row['server_header']!r}",
            flush=True,
        )
        if dry_run or i == fetches_per_source - 1:
            break
        time.sleep(spacing_seconds)


def main() -> int:
    ap = argparse.ArgumentParser(description="Akamai Egress Spike — Actions lane probe.")
    ap.add_argument(
        "--duration", type=int, default=3600,
        help="Total wall-clock seconds for the spike (default 3600 = 1 hour).",
    )
    ap.add_argument(
        "--fetches-per-source", type=int, default=100,
        help="How many fetches per source URL (default 100).",
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Hit each target ONCE then exit. No sleep, no full window.",
    )
    args = ap.parse_args()

    probe = _load_probe_sources()
    targets: list[str] = probe["probe_targets"]
    user_agent: str = probe["user_agent"]

    if args.dry_run:
        spacing = 0.0
        fetches = 1
        print(f"DRY RUN — single fetch per target ({len(targets)} targets)", flush=True)
    else:
        # Spread N fetches across the requested duration window per source.
        fetches = args.fetches_per_source
        spacing = max(1.0, args.duration / fetches)
        print(
            f"Spike start — {fetches} fetches × {len(targets)} targets, "
            f"spacing {spacing:.1f}s, total window ≈ {args.duration}s ({args.duration / 60:.1f} min).",
            flush=True,
        )

    # Ensure results.json exists with the right skeleton so concurrent appends are safe.
    if not RESULTS_FILE.exists():
        RESULTS_FILE.write_text(
            json.dumps({"worker_lane": [], "actions_lane": []}, indent=2),
            encoding="utf-8",
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(targets)) as pool:
        futures = [
            pool.submit(_drive_one_source, t, user_agent, fetches, spacing, args.dry_run)
            for t in targets
        ]
        for f in concurrent.futures.as_completed(futures):
            exc = f.exception()
            if exc:
                print(f"WARN — worker thread raised: {exc!r}", file=sys.stderr, flush=True)

    print(f"\nDone. Raw rows appended to {RESULTS_FILE}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
