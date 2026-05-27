#!/usr/bin/env python3
# Phase 2 fidelity-text drift CI gate. See .planning/REQUIREMENTS.md INF-05.
"""Verify that every fidelity sample round-trips byte-equivalent on a live URL.

Fetches each unique `source_path` recorded in `tests/fidelity-samples.json`
from a configurable base URL (default: CF Pages preview at
`https://realufo.pages.dev`), re-extracts the same text-node selectors that
`scripts/extract-fidelity-samples.py` used at lock time, then asserts the
fetched text matches the locked `expected_text` byte-for-byte after
stripping leading/trailing whitespace ONLY — no smart-quote folding, no
accent normalisation, no em-dash collapsing. See D-20 (Phase 2 CONTEXT).

Per research/PITFALLS.md Pitfall #4, this is the gate that catches a
markdown processor "improving" `"` → `"` or producing `Ã©` mojibake from a
mis-decoded UTF-8 byte sequence. CLAUDE.md §9 mandates verbatim official
text for every archive's hero lede, footer license attribution, and card
catalog titles; the SSG output (Phase 3+) must preserve those bytes exactly.

Failure mode (D-21): emit a `difflib.unified_diff` per mismatched sample —
loud, granular, line-level. CI prints the diffs in the PR log so the
operator can immediately see which selector drifted and what changed.

CLI:
    python3 scripts/verify-fidelity.py
        # Default base URL = https://realufo.pages.dev (CF Pages preview)
    python3 scripts/verify-fidelity.py --base-url https://realufo.org
        # Sanity: same content as main → exit 0
    python3 scripts/verify-fidelity.py --base-url https://X.pages.dev --color
        # CI: PR-preview URL + ANSI-colored diff in the log
    python3 scripts/verify-fidelity.py --archive aaro
        # Run only AARO's samples (local debug)
    python3 scripts/verify-fidelity.py --kind hero-lede
        # Run only hero-lede samples across all archives

Exit codes (per snapshot-urls.py convention):
    0 — every sample matched byte-equivalent.
    1 — at least one sample drifted (unified diff printed per failure).
    2 — fetch error / samples file missing / unreadable.

Stdlib only — `argparse`, `difflib`, `json`, `pathlib`, `re`, `sys`,
`urllib.request`, `urllib.error`, `html.parser.HTMLParser`. The HTMLParser-
based text extractors are duplicated verbatim from
`scripts/extract-fidelity-samples.py` — Python file names with hyphens are
not importable as modules. Per .planning/codebase/CONVENTIONS.md, sharing
a third helper module would require renaming both scripts; cleaner to keep
each script standalone with duplicated text extractors. **Keep the two
copies in sync.**
"""
from __future__ import annotations

# Shared with scripts/extract-fidelity-samples.py — keep in sync.

import argparse
import difflib
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser

REPO = pathlib.Path(__file__).resolve().parent.parent
SAMPLES = REPO / 'tests' / 'fidelity-samples.json'
DEFAULT_BASE = 'https://realufo.pages.dev'
USER_AGENT = 'realufo-fidelity-gate/1.0 (+https://github.com/hectorchanht/gov-ufo-archive)'
FETCH_TIMEOUT_S = 30

# Inline JSON manifest regex (mirrors scripts/extract-fidelity-samples.py + snapshot-urls.py).
# Phase 4 Plan 04-05 [Rule 1] — relaxed to tolerate attribute order swaps.
# Astro's HTML compiler emits `<script type="application/json" id="...">`,
# whereas the legacy Python build scripts emitted `id="..." type="application/json"`.
# Pattern allows ANY attribute between `<script` and the closing `>` so both
# attribute orderings parse identically.
MANIFEST_RE = re.compile(
    r'<script[^>]*id="(?:arch-data|archive-manifest)"[^>]*>(.*?)</script>',
    re.DOTALL,
)

# ANSI escape codes for --color diff output.
ANSI_RED = '\033[31m'
ANSI_GREEN = '\033[32m'
ANSI_CYAN = '\033[36m'
ANSI_BOLD = '\033[1m'
ANSI_RESET = '\033[0m'


# --- HTMLParser-based text extraction ---------------------------------------
# DUPLICATED from scripts/extract-fidelity-samples.py — keep in sync.

class _TagTextCollector(HTMLParser):
    """Collect inner text of the first element matching tag + class predicate."""

    def __init__(self, tag: str, want_class: str | None):
        super().__init__(convert_charrefs=True)
        self._target_tag = tag
        self._target_class = want_class
        self._stack: list[tuple[str, set[str]]] = []
        self._buf: list[str] = []
        self._inside_at: int = -1
        self._captured: bool = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes: set[str] = set()
        for name, value in attrs:
            if name == 'class' and value:
                classes = set(value.split())
                break
        self._stack.append((tag, classes))
        if (
            not self._captured
            and self._inside_at < 0
            and tag == self._target_tag
            and (self._target_class is None or self._target_class in classes)
        ):
            self._inside_at = len(self._stack) - 1

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                if self._inside_at >= 0 and i == self._inside_at:
                    self._captured = True
                    self._inside_at = -1
                del self._stack[i:]
                break

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        return

    def handle_data(self, data: str) -> None:
        if self._inside_at >= 0 and not self._captured:
            self._buf.append(data)

    def result(self) -> str | None:
        if not self._buf:
            return None
        return ''.join(self._buf)


def extract_inner_text(html: str, tag: str, want_class: str | None) -> str | None:
    """Return the inner text of the first `<tag class="...">` match, or None."""
    parser = _TagTextCollector(tag, want_class)
    try:
        parser.feed(html)
    except Exception as exc:  # pragma: no cover
        print(f'warning: HTMLParser failed: {exc}', file=sys.stderr)
        return None
    text = parser.result()
    if text is None:
        return None
    return text.strip()


def first_card_titles(html: str, n: int = 5) -> list[str]:
    """Parse the inline arch-data / archive-manifest JSON, return first N titles verbatim."""
    out: list[str] = []
    for match in MANIFEST_RE.finditer(html):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            print(f'warning: failed to parse inline manifest: {exc}', file=sys.stderr)
            continue
        records: list = []
        if isinstance(data, dict):
            if isinstance(data.get('assets'), list):
                records = data['assets']
            elif isinstance(data.get('rows'), list):
                records = data['rows']
        for record in records:
            if not isinstance(record, dict):
                continue
            title: str | None = None
            for key in ('ti', 'Title', 'title', 'Video Title'):
                value = record.get(key)
                if isinstance(value, str) and value.strip():
                    title = value
                    break
            if title is None:
                continue
            out.append(title)
            if len(out) >= n:
                return out
    return out


class _FooterParagraphFinder(HTMLParser):
    """Collect text of every `<p>` (and `<small>`) inside the first `<footer>`."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_footer_depth = 0
        self._in_para = False
        self._buf: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == 'footer':
            self._in_footer_depth += 1
            return
        if self._in_footer_depth > 0 and tag in ('p', 'small'):
            self._in_para = True
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ('p', 'small') and self._in_para:
            text = ''.join(self._buf).strip()
            text = re.sub(r'\s+', ' ', text)
            if text:
                self.paragraphs.append(text)
            self._in_para = False
            self._buf = []
            return
        if tag == 'footer' and self._in_footer_depth > 0:
            self._in_footer_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_para:
            self._buf.append(data)


LICENSE_MARKERS_BY_ARCHIVE: dict[str, tuple[str, ...]] = {
    'wargov':    ('17 U.S.C.', 'public domain', 'Public Domain', 'Public domain'),
    'aaro':      ('17 U.S.C.',),
    'nasa':      ('17 U.S.C.',),
    'nara':      ('17 U.S.C.',),
    'geipan':    ('Loi n° 78-753', 'Loi n°'),
    'uk':        ('Open Government Licence',),
    'brazil':    ('Lei nº 12.527', 'LAI'),
    'chile':     ('Ley nº 20.285', 'Ley n° 20.285'),
    'argentina': ('Ley nº 27.275', 'Ley n° 27.275', 'Ley 27.275'),
    'canada':    ('Crown Copyright', 'Government of Canada', 'public domain', 'Public domain'),
    'italy':     ('D.lgs. 33/2013', 'D.lgs.'),
    'nz':        ('Crown Copyright', 'Crown copyright', 'Creative Commons'),
    'peru':      ('Ley nº 27806', 'Ley n° 27806', 'reusable'),
    'spain':     ('Ley 19/2013',),
    'uruguay':   ('Ley nº 18.381', 'Ley n° 18.381'),
}


def extract_license_footer(html: str, archive: str) -> str | None:
    """Return the verbatim license paragraph from the first `<footer>`, or None."""
    finder = _FooterParagraphFinder()
    try:
        finder.feed(html)
    except Exception as exc:  # pragma: no cover
        print(f'warning: footer parse failed for {archive}: {exc}', file=sys.stderr)
        return None
    markers = LICENSE_MARKERS_BY_ARCHIVE.get(archive, ())
    for para in finder.paragraphs:
        for marker in markers:
            if marker in para:
                return para
    if finder.paragraphs:
        return finder.paragraphs[0]
    return None


class _SectionHeadingFinder(HTMLParser):
    """Collect (heading-text, following-paragraph-text) pairs from <h2> + <p>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_h2 = False
        self._in_p_after_h2 = False
        self._h2_buf: list[str] = []
        self._p_buf: list[str] = []
        self._last_h2: str | None = None
        self.entries: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == 'h2':
            self._in_h2 = True
            self._h2_buf = []
        elif tag == 'p' and self._last_h2 is not None and not self._in_p_after_h2:
            self._in_p_after_h2 = True
            self._p_buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == 'h2' and self._in_h2:
            self._in_h2 = False
            heading = ''.join(self._h2_buf).strip()
            heading = re.sub(r'\s+', ' ', heading)
            self._last_h2 = heading or None
        elif tag == 'p' and self._in_p_after_h2:
            self._in_p_after_h2 = False
            para = ''.join(self._p_buf).strip()
            para = re.sub(r'\s+', ' ', para)
            if self._last_h2 and para:
                self.entries.append((self._last_h2, para))
            self._last_h2 = None

    def handle_data(self, data: str) -> None:
        if self._in_h2:
            self._h2_buf.append(data)
        elif self._in_p_after_h2:
            self._p_buf.append(data)


# --- Re-extraction dispatcher ---------------------------------------------

def re_extract_text(html: str, sample: dict) -> str | None:
    """Re-derive the live text for one sample from the fetched HTML.

    Dispatch by `kind`:
      - hero-lede      → extract_inner_text(html, 'h1', 'hero-title')
      - hero-sub       → extract_inner_text(html, 'p',  'hero-sub') + ws-collapse
      - license-footer → extract_license_footer(html, archive)
      - faq-answer     → /about.html h2 → first-following-p (indexed by selector)
      - card-title     → first_card_titles(html, n=index+1)[index]
    """
    kind = sample['kind']
    if kind == 'hero-lede':
        return extract_inner_text(html, 'h1', 'hero-title')
    if kind == 'hero-sub':
        sub = extract_inner_text(html, 'p', 'hero-sub')
        if sub is None:
            return None
        return re.sub(r'\s+', ' ', sub)
    if kind == 'license-footer':
        return extract_license_footer(html, sample['archive'])
    if kind == 'card-title':
        # Selector shape: `script#arch-data[<idx>].ti`
        match = re.search(r'\[(\d+)\]', sample['selector'])
        if match is None:
            return None
        idx = int(match.group(1))
        titles = first_card_titles(html, n=idx + 1)
        if idx >= len(titles):
            return None
        return titles[idx]
    if kind == 'faq-answer':
        finder = _SectionHeadingFinder()
        try:
            finder.feed(html)
        except Exception as exc:  # pragma: no cover
            print(f'warning: faq parse failed: {exc}', file=sys.stderr)
            return None
        match = re.search(r'h2#(\d+)', sample['selector'])
        if match is None:
            return None
        idx = int(match.group(1))
        if idx >= len(finder.entries):
            return None
        return finder.entries[idx][1]
    print(f'warning: unknown sample kind {kind!r}', file=sys.stderr)
    return None


# --- Fetching --------------------------------------------------------------

def fetch_page(url: str) -> str:
    """HTTP GET → str. Raises urllib.error.URLError on fetch failure."""
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT_S) as response:  # nosec B310
        # CF Pages serves UTF-8; respect the Content-Type charset if declared.
        charset = response.headers.get_content_charset() or 'utf-8'
        body = response.read()
    return body.decode(charset, errors='replace')


# --- Diff rendering --------------------------------------------------------

def format_diff(expected: str, actual: str, label_from: str, label_to: str, color: bool) -> str:
    """Render a unified diff between expected and actual text.

    The diff is line-oriented (splitlines). Each text is split on '\\n' so
    multi-line samples (license-footer, hero-sub) produce per-line diff
    output. Single-line samples produce a one-hunk diff with a single
    replacement line — still readable in the PR log.
    """
    diff_lines = list(difflib.unified_diff(
        expected.splitlines(keepends=False),
        actual.splitlines(keepends=False),
        fromfile=label_from,
        tofile=label_to,
        lineterm='',
        n=1,
    ))
    if not color:
        return '\n'.join(diff_lines)
    out = []
    for line in diff_lines:
        if line.startswith('+++') or line.startswith('---'):
            out.append(f'{ANSI_BOLD}{line}{ANSI_RESET}')
        elif line.startswith('@@'):
            out.append(f'{ANSI_CYAN}{line}{ANSI_RESET}')
        elif line.startswith('+'):
            out.append(f'{ANSI_GREEN}{line}{ANSI_RESET}')
        elif line.startswith('-'):
            out.append(f'{ANSI_RED}{line}{ANSI_RESET}')
        else:
            out.append(line)
    return '\n'.join(out)


# --- CLI entry -------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description='Verify fidelity samples round-trip byte-equivalent against a live URL.',
    )
    parser.add_argument(
        '--base-url', default=DEFAULT_BASE,
        help=f'Base URL to fetch each sample from (default: {DEFAULT_BASE}).',
    )
    parser.add_argument(
        '--color', action='store_true',
        help='ANSI-colour the unified diff output (use in CI logs that render colour).',
    )
    parser.add_argument(
        '--archive', default=None,
        help='Only verify samples for this archive slug (e.g. aaro, geipan).',
    )
    parser.add_argument(
        '--kind', default=None,
        help='Only verify samples of this kind (hero-lede / hero-sub / license-footer / faq-answer / card-title).',
    )
    parser.add_argument(
        '--strip-leading-trailing-whitespace-only', dest='strip_only',
        action='store_true', default=True,
        help=(
            'Documents D-20: leading/trailing whitespace is the ONLY normalisation '
            'applied before comparison. Always enabled — flag exists to make the rule visible.'
        ),
    )
    args = parser.parse_args()

    if not SAMPLES.exists():
        print(f'error: {SAMPLES} not found — run scripts/extract-fidelity-samples.py first.', file=sys.stderr)
        return 2
    try:
        samples = json.loads(SAMPLES.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        print(f'error: cannot read {SAMPLES}: {exc}', file=sys.stderr)
        return 2

    # Filter by --archive / --kind if given.
    if args.archive:
        samples = [s for s in samples if s['archive'] == args.archive]
    if args.kind:
        samples = [s for s in samples if s['kind'] == args.kind]
    if not samples:
        print('error: no samples match the filters.', file=sys.stderr)
        return 2

    # Group by source_path so we fetch each page only once.
    by_path: dict[str, list[dict]] = {}
    for sample in samples:
        by_path.setdefault(sample['source_path'], []).append(sample)

    base = args.base_url.rstrip('/')
    passed = 0
    failures: list[tuple[dict, str, str]] = []  # (sample, expected, actual)

    for path in sorted(by_path):
        url = base + path
        try:
            html = fetch_page(url)
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f'[FETCH-FAIL] {url}: {exc}', file=sys.stderr)
            return 2
        for sample in by_path[path]:
            actual = re_extract_text(html, sample)
            if actual is None:
                failures.append((sample, sample['expected_text'], '<not found>'))
                print(f'  [FAIL]  {sample["archive"]}/{sample["kind"]} ({sample["selector"]}) — selector returned nothing.')
                continue
            # D-20: strip leading/trailing whitespace ONLY. No other normalisation.
            expected_stripped = sample['expected_text'].strip()
            actual_stripped = actual.strip()
            if expected_stripped == actual_stripped:
                passed += 1
                print(f'  [ok]    {sample["archive"]}/{sample["kind"]}')
            else:
                failures.append((sample, expected_stripped, actual_stripped))
                print(f'  [FAIL]  {sample["archive"]}/{sample["kind"]} ({sample["selector"]})')

    total = len(samples)
    print()
    print(f'{passed}/{total} samples matched.')
    if failures:
        print()
        print(f'{len(failures)} failure(s):')
        for sample, expected, actual in failures:
            label_from = f'{sample["archive"]}/{sample["kind"]}/expected'
            label_to = f'{sample["archive"]}/{sample["kind"]}/actual'
            print()
            print(format_diff(expected, actual, label_from, label_to, args.color))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
