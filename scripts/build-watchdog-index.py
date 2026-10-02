#!/usr/bin/env python3
"""build-watchdog-index.py — emit dist/watchdog.json for the realufo-watchdog Worker.

Run as a postbuild step (invoked from scripts/copy-legacy-archives.sh).

Output (dist/watchdog.json):
  assets              every R2 key the site links to (assets.realufo.org/<key>),
                      scraped from data/*.json — the Worker diffs these
                      against the R2 bucket listing to find 404s.
  wargovReleaseDates  distinct "Release Date" values in uap-data.csv — the
                      Worker flags any war.gov CSV date not in this list as
                      a new release.

Shipping it with the site means the Worker's expected state always matches
what is deployed, with no redeploy of the Worker per release.

CLAUDE.md §13 — Phase-4 Python carve-out (infra script, not a page builder).
"""

import csv
import json
import re
from pathlib import Path
from urllib.parse import unquote

REPO = Path(__file__).resolve().parent.parent
# Keys may contain spaces and apostrophes ("18_100754_ general 1946-7_vol_2.jpg"),
# and some sit inside HTML strings (src="…"), so match on parsed string values
# and stop only at a quote / tag bracket / newline.
ASSET_RE = re.compile(r'https://assets\.realufo\.org/([^"<>\n?#]+)')


def strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from strings(v)


keys = set()
for f in sorted((REPO / "data").glob("*.json")):
    for s in strings(json.loads(f.read_text(encoding="utf-8"))):
        keys.update(unquote(k.strip()) for k in ASSET_RE.findall(s))

with open(REPO / "uap-data.csv", encoding="utf-8-sig", newline="") as fh:
    dates = {r["Release Date"].strip() for r in csv.DictReader(fh) if r.get("Release Date", "").strip()}

out = REPO / "dist" / "watchdog.json"
out.write_text(json.dumps({"assets": sorted(keys), "wargovReleaseDates": sorted(dates)}), encoding="utf-8")
print(f"[postbuild] wrote dist/watchdog.json ({len(keys)} assets, {len(dates)} release dates)")
