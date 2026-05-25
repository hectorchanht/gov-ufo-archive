#!/usr/bin/env python3
# Generated input for Cloudflare Pages routing. See .planning/REQUIREMENTS.md INF-02.
"""Generate the Cloudflare Pages `_redirects` file from `URL-CONTRACT.txt`.

Purpose (INF-02 — the `_redirects` half; `_headers` shipped in Plan 02-01):
walk every canonical route in `URL-CONTRACT.txt` and emit one explicit
`<source> <destination> <status>` line per route so Cloudflare Pages
serves the URL contract verbatim from day one.

Why per-route explicit lines:
  - CF Pages' default behaviour for unmatched paths is `302`. Phase 2
    decision D-10 mandates explicit overrides (`200` rewrite, `301`
    canonical redirect) so SEO equity and browser-bar URLs match the
    contract. See `.planning/research/PITFALLS.md` §Pitfall #8 / #11
    for the syntax gotchas (space-delimited, one rule per line, no
    commas; CF Pages silently drops malformed rules).
  - `200` (rewrite) keeps the URL in the browser bar; no actual
    redirect hop. Every canonical route is emitted as `P P 200`.
  - For directory routes (`/aaro/`) we also emit a `301` from the
    unslashed form (`/aaro`) to the canonical with-slash form. CF
    Pages otherwise treats `/aaro` and `/aaro/` as distinct
    (Specifics §2 in 02-CONTEXT.md).

Why URL-CONTRACT.txt as input:
  - D-09 / D-11 invariant: `_redirects` is exclusively generator
    output. Hand-editing is forbidden — drift is caught by the
    `--check` CI gate added in Plan 02-08.
  - URL-CONTRACT.txt is the locked Phase 1 PMS-01 deliverable. Any
    URL surface change MUST land via snapshot-urls.py first.

What it walks:
  - Lines starting with `/` in URL-CONTRACT.txt.
  - Per-card `#card-<slug>` anchors are stripped before deduping —
    anchors live on their parent page route (which IS emitted) and
    individually-emitting ~4800 fragment rules would burn through the
    CF Pages 2000-rule limit.

CLI:
    python3 scripts/build-redirects.py             # write _redirects
    python3 scripts/build-redirects.py --stdout    # print, do not write
    python3 scripts/build-redirects.py --check     # CI: exit 1 on drift

`--check` strips the volatile `# Generated ... @ <sha> on <date>` line
from both the freshly-rendered text and the on-disk file before
comparing — mirrors `scripts/snapshot-urls.py`'s `_strip_volatile_header`
helper so that the SHA advancing past the regen commit does not make
the file eternally "stale" against itself.

Exit codes:
    0 — wrote (or matched) _redirects successfully.
    1 — `--check` found structural drift vs URL-CONTRACT.txt.
    2 — input URL-CONTRACT.txt missing or unreadable.

Stdlib only — `argparse`, `datetime`, `os`, `pathlib`, `re`, `subprocess`,
`sys`. Matches the stdlib-only convention from CLAUDE.md §6.2 and the
shape of `scripts/snapshot-urls.py`.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
INPUT = REPO / 'URL-CONTRACT.txt'
OUTPUT = REPO / '_redirects'

# Strip after first `#` — drops `#card-<slug>` anchors so the parent
# page route is emitted exactly once.
FRAGMENT_RE = re.compile(r'#.*$')

# Matches the auto-generated `# Generated ... @ <sha> on <YYYY-MM-DD>` line.
# Used by `_strip_volatile_header` so `--check` ignores stamp drift across
# regen runs that change only the SHA / date but not the structural body.
# Mirrors the helper pattern in scripts/snapshot-urls.py.
VOLATILE_HEADER_RE = re.compile(r'^# Generated.*@.*on \d{4}')


def short_sha() -> str:
    """Return the current HEAD short SHA, or `unknown` if git is unavailable."""
    try:
        out = subprocess.run(
            ['git', '-C', str(REPO), 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, check=True, timeout=3,
        ).stdout.strip()
        return out or 'unknown'
    except Exception:
        return 'unknown'


def load_routes() -> list[str]:
    """Return the sorted, deduped list of canonical routes from URL-CONTRACT.txt.

    Steps:
      1. Read INPUT; iterate lines.
      2. Skip blank lines and `# ...` headers.
      3. For each `/`-prefixed line: strip everything from the first `#`
         onward (drops per-card anchors); add to a set.
      4. Return sorted list.

    If INPUT is missing or unreadable, print to stderr and exit 2.
    """
    if not INPUT.exists():
        print(f'URL-CONTRACT.txt missing at {INPUT}', file=sys.stderr)
        sys.exit(2)
    try:
        text = INPUT.read_text(encoding='utf-8')
    except OSError as exc:
        print(f'cannot read URL-CONTRACT.txt at {INPUT}: {exc}', file=sys.stderr)
        sys.exit(2)

    routes: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if not line.startswith('/'):
            continue
        path = FRAGMENT_RE.sub('', line)
        if not path:
            continue
        routes.add(path)
    return sorted(routes)


def emit_rule(src: str, dst: str, status: int) -> str:
    """Format a single CF Pages redirect rule line.

    CF Pages syntax: space-delimited, one rule per line, no commas
    (research/PITFALLS.md §Pitfall #8 — comma-delimited Netlify-style
    syntax is silently dropped).
    """
    return f'{src} {dst} {status}'


def _strip_volatile_header(text: str) -> str:
    """Drop lines matching VOLATILE_HEADER_RE so --check compares structure only.

    The `# Generated by ... @ <sha> on <date>` line changes every regen
    (SHA advances; date may roll over). Comparing it byte-for-byte
    would mean `--check` is unsatisfiable as soon as the regen commit
    itself lands (HEAD moves; next regen records the new SHA). The
    structural body — the sorted rule list — is what the CI drift gate
    actually polices. Mirrors `_strip_volatile_header` in
    `scripts/snapshot-urls.py`.

    Static comment lines (`# DO NOT EDIT ...`, `# Status codes: ...`)
    are NOT volatile and remain in the diff input.
    """
    lines = []
    for line in text.splitlines(keepends=True):
        if VOLATILE_HEADER_RE.match(line):
            continue
        lines.append(line)
    return ''.join(lines)


def render_redirects(routes: list[str]) -> str:
    """Render the full `_redirects` body for `routes`.

    Header:
      Line 1 (VOLATILE):  `# Generated by scripts/build-redirects.py from URL-CONTRACT.txt @ <sha> on <date>`
      Line 2 (STATIC):    `# DO NOT EDIT — re-run scripts/build-redirects.py (D-09 / D-11)`
      Line 3 (STATIC):    `# Status codes — 200 = rewrite (URL stays); 301 = permanent redirect.`
      Line 4 (STATIC):    blank

    Note: comment lines avoid commas so a literal `grep -q ','` over
    the whole file (Plan 02-05 verify clause) only ever matches a rule
    body — which itself never contains commas (CF Pages uses
    space-delimited tokens per PITFALLS #8).

    Body — for each route P (sorted):
      `P P 200`  (rewrite — CF Pages keeps URL in browser bar; overrides default 302)
      If P endswith `/` and P != `/`:
        `<P_without_slash> P 301`  (trailing-slash canonicalization)

    File-style routes (`/foo.html`) stay as-is; CF Pages serves the file
    directly. No 301 emitted for them.
    """
    sha = short_sha()
    date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')

    lines: list[str] = []
    lines.append(f'# Generated by scripts/build-redirects.py from URL-CONTRACT.txt @ {sha} on {date}')
    lines.append('# DO NOT EDIT — re-run scripts/build-redirects.py (D-09 / D-11)')
    lines.append('# Status codes — 200 = rewrite (URL stays); 301 = permanent redirect.')
    lines.append('')

    for route in routes:
        lines.append(emit_rule(route, route, 200))
        if route.endswith('/') and route != '/':
            unslashed = route[:-1]
            lines.append(emit_rule(unslashed, route, 301))

    return '\n'.join(lines) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Generate Cloudflare Pages _redirects from URL-CONTRACT.txt.',
    )
    parser.add_argument(
        '--stdout', action='store_true',
        help='Print the generated _redirects to stdout instead of writing the file.',
    )
    parser.add_argument(
        '--check', action='store_true',
        help='Regenerate in memory and exit non-zero if _redirects is stale.',
    )
    args = parser.parse_args()

    routes = load_routes()
    text = render_redirects(routes)

    rule_count = text.count('\n') - 4  # subtract 3 header lines + 1 trailing newline
    rewrite_count = sum(1 for r in routes)
    redirect_count = sum(1 for r in routes if r.endswith('/') and r != '/')

    if args.stdout:
        sys.stdout.write(text)
        return 0

    if args.check:
        if not OUTPUT.exists():
            print(f'_redirects missing at {OUTPUT}', file=sys.stderr)
            return 1
        try:
            existing = OUTPUT.read_text(encoding='utf-8')
        except OSError as exc:
            print(f'cannot read _redirects at {OUTPUT}: {exc}', file=sys.stderr)
            return 1
        # Strip volatile sha+date stamp from BOTH sides before structural diff.
        if _strip_volatile_header(existing) != _strip_volatile_header(text):
            print('_redirects is stale — re-run scripts/build-redirects.py', file=sys.stderr)
            return 1
        print(
            f'_redirects up-to-date ({len(routes)} canonical routes, '
            f'{rewrite_count + redirect_count} rules: '
            f'{rewrite_count} rewrites + {redirect_count} trailing-slash redirects).'
        )
        return 0

    OUTPUT.write_text(text, encoding='utf-8')
    print(
        f'Wrote _redirects — {len(routes)} canonical routes, '
        f'{rewrite_count + redirect_count} rules '
        f'({rewrite_count} rewrites + {redirect_count} trailing-slash redirects).'
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
