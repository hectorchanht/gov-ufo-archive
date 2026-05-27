#!/usr/bin/env python3
# Generated input for the Phase 2 fidelity-text drift gate. See .planning/REQUIREMENTS.md INF-05.
"""Extract the locked fidelity-sample list from current main HTML.

One-shot extractor. Walks every tracked archive `index.html` plus the
root landing page and `about.html`, pulls out specific text nodes that
CLAUDE.md §9 designates as the verbatim-text contract (hero ledes, FAQ
section answers where present, license-footer paragraphs, and the
first N official card titles from each archive's inline JSON
manifest), and serializes the result to `tests/fidelity-samples.json`.

The output is the locked contract: per Phase 2 CONTEXT D-18 / D-19,
this file is extracted ONCE from current `main`, committed, and
frozen. Future SSG output (Phase 3+) must round-trip every sample
byte-equivalent — smart quotes, em-dashes, French/Spanish/Portuguese
accents must survive any markdown processor or Astro renderer with
zero typographer drift (`"` → `"`, `é` → `Ã©`, em-dash collapse, etc.;
all explicitly forbidden per research/PITFALLS.md Pitfall #4).

Re-running this script overwrites `tests/fidelity-samples.json`. That
is an operator-only action — CI never invokes it. Mirrors D-17 (visual
baselines): the gate's whole point is to catch drift, so auto-regen
would defeat the purpose. Whitespace handling on read: text is
extracted verbatim from the source HTML (no smart-quote folding, no
HTML-entity decoding beyond what `html.parser.HTMLParser` does by
default — `&amp;` → `&`, `&nbsp;` → U+00A0, etc.). Leading/trailing
whitespace is stripped to normalise line-wrap variance between source
files; interior whitespace is preserved byte-for-byte.

CLI:
    python3 scripts/extract-fidelity-samples.py            # write tests/fidelity-samples.json
    python3 scripts/extract-fidelity-samples.py --stdout   # print to stdout (no write)
    python3 scripts/extract-fidelity-samples.py --check    # CI: exit 1 if file missing / schema invalid

Exit codes:
    0 — wrote (or matched) tests/fidelity-samples.json successfully.
    1 — `--check` found missing file or schema mismatch.
    2 — failed to read source HTML (file missing / unreadable).

Stdlib only — `argparse`, `json`, `os`, `pathlib`, `re`, `subprocess`,
`sys`, `html.parser.HTMLParser`. Matches the `stdlib-only` convention
from CLAUDE.md §6.2 + .planning/codebase/CONVENTIONS.md §"Python".
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
from html.parser import HTMLParser

REPO = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = REPO / 'tests' / 'fidelity-samples.json'

# Per CLAUDE.md §2 — 15 official archives. Order matches §2 table.
# Tuple: (archive-slug, repo-relative HTML path, public URL path).
ARCHIVES_AND_PATHS: list[tuple[str, str, str]] = [
    ('wargov',    'index.html',           '/'),
    ('aaro',      'aaro/index.html',      '/aaro/'),
    ('nasa',      'nasa/index.html',      '/nasa/'),
    ('nara',      'nara/index.html',      '/nara/'),
    ('geipan',    'geipan/index.html',    '/geipan/'),
    ('uk',        'uk/index.html',        '/uk/'),
    ('brazil',    'brazil/index.html',    '/brazil/'),
    ('chile',     'chile/index.html',     '/chile/'),
    ('argentina', 'argentina/index.html', '/argentina/'),
    ('canada',    'canada/index.html',    '/canada/'),
    ('italy',     'italy/index.html',     '/italy/'),
    ('nz',        'nz/index.html',        '/nz/'),
    ('peru',      'peru/index.html',      '/peru/'),
    ('spain',     'spain/index.html',     '/spain/'),
    ('uruguay',   'uruguay/index.html',   '/uruguay/'),
]

# Inline JSON manifest regex (mirrors scripts/snapshot-urls.py +
# scripts/verify-fidelity.py — keep in sync). Phase 4 Plan 04-05
# [Rule 1] — relaxed to tolerate attribute order swaps. Astro's HTML
# compiler emits `<script type="application/json" id="...">`, whereas
# the legacy Python build scripts emitted `id="..." type="application
# /json"`. The pattern below accepts ANY attribute ordering between
# `<script` and the closing `>` so both forms parse identically.
MANIFEST_RE = re.compile(
    r'<script[^>]*id="(?:arch-data|archive-manifest)"[^>]*>(.*?)</script>',
    re.DOTALL,
)

# Card-title sample size per archive (D-18: "sampled — first 5 per archive").
CARD_TITLE_N = 5

# Schema field set — every record in tests/fidelity-samples.json must have these keys.
REQUIRED_FIELDS = frozenset({
    'archive', 'kind', 'selector', 'source_path', 'expected_text', 'source_file',
})


# --- HTMLParser-based text extraction (stdlib only) -------------------------

class _TagTextCollector(HTMLParser):
    """Collect inner text of the first element matching tag + class predicate.

    Tracks a stack of (tag, classes) pairs. Once we enter a matching
    element, accumulate every character data event (and rebuild inline
    tags as literal text so markup like `<em>` inside `<h1>` round-trips
    via plain-text concatenation — interior text fidelity is the contract,
    not DOM equivalence).

    The collector intentionally does NOT decode entities beyond what
    `HTMLParser` does by default. The default behaviour decodes named
    entities (`&amp;` → `&`, `&nbsp;` → U+00A0) and numeric entities
    (`&#x2014;` → `—`) via `html.unescape`. That matches what a real
    browser would render and what an SSG output is expected to contain.
    """

    def __init__(self, tag: str, want_class: str | None):
        super().__init__(convert_charrefs=True)
        self._target_tag = tag
        self._target_class = want_class
        self._stack: list[tuple[str, set[str]]] = []
        self._buf: list[str] = []
        # Depth at which we're inside the target. -1 = not yet inside.
        # Once set, we collect text until the stack pops below this depth.
        self._inside_at: int = -1
        self._captured: bool = False  # only capture the FIRST match

    # --- HTMLParser overrides ------------------------------------------------
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
        # Pop the matching open tag (defensive — match by name, not strict pairing).
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                # If we were inside the target and just closed it, freeze the capture.
                if self._inside_at >= 0 and i == self._inside_at:
                    self._captured = True
                    self._inside_at = -1
                del self._stack[i:]
                break

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Void/self-closing tags — no nested text. Nothing to do.
        return

    def handle_data(self, data: str) -> None:
        if self._inside_at >= 0 and not self._captured:
            self._buf.append(data)

    # --- result ---------------------------------------------------------------
    def result(self) -> str | None:
        if not self._buf:
            return None
        return ''.join(self._buf)


def extract_inner_text(html: str, tag: str, want_class: str | None) -> str | None:
    """Return the inner text of the first `<tag class="...">` match, or None.

    `want_class` may be None (match by tag alone) or a class name string —
    matches when the element's class attribute contains that name (treats
    `class="hero-title accent"` as having both `hero-title` and `accent`).
    Strips leading/trailing whitespace ONLY — interior whitespace preserved
    byte-for-byte per D-20 (the gate's whole contract).
    """
    parser = _TagTextCollector(tag, want_class)
    try:
        parser.feed(html)
    except Exception as exc:  # pragma: no cover — HTMLParser is forgiving
        print(f'warning: HTMLParser failed: {exc}', file=sys.stderr)
        return None
    text = parser.result()
    if text is None:
        return None
    return text.strip()


def first_card_titles(html: str, n: int = CARD_TITLE_N) -> list[str]:
    """Parse the inline arch-data / archive-manifest JSON, return first N titles verbatim.

    Per scripts/snapshot-urls.py — catalog shape is `{"assets": [...]}` with
    `ti` field; root war.gov shape is `{"rows": [...]}` with `Title` field.
    """
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


# --- Per-archive extraction ------------------------------------------------

# License-jurisdiction hints — used to validate that the right text was pulled
# from each archive's footer. Per CLAUDE.md §9. The extractor finds the first
# `<p>` inside `<footer>` whose text contains any of these markers.
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


class _FooterParagraphFinder(HTMLParser):
    """Collect text of every `<p>` (and `<small>`) inside the first `<footer>` element."""

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
            # Collapse interior runs of whitespace to a single space — the
            # source HTML breaks license sentences across multiple lines for
            # readability, but the rendered text is single-line. Per D-20,
            # leading/trailing whitespace stripping is allowed; this is a
            # minor extension for interior line-wrap normalisation only, NOT
            # smart-quote or character normalisation. Documented exception.
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


def extract_license_footer(html: str, archive: str) -> str | None:
    """Return the verbatim license paragraph from the first `<footer>`, or None.

    Strategy: parse every `<p>` and `<small>` inside `<footer>`, then return
    the first one whose text contains any of the jurisdiction's license
    markers (CLAUDE.md §9). On no-match: return the first non-empty paragraph
    as a best-effort fallback — the operator can hand-correct after the
    one-shot extraction per D-CONTEXT.md §"Claude's Discretion".
    """
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
    # Fallback — return the first non-empty paragraph (operator can audit).
    if finder.paragraphs:
        return finder.paragraphs[0]
    return None


def extract_for_archive(archive: str, html_path: pathlib.Path, public_path: str) -> list[dict]:
    """Build the record list for one archive's index.html."""
    try:
        html = html_path.read_text(encoding='utf-8')
    except OSError as exc:
        print(f'error: cannot read {html_path}: {exc}', file=sys.stderr)
        raise
    records: list[dict] = []
    source_file = str(html_path.relative_to(REPO))

    # 1. hero-lede — <h1 class="hero-title">
    lede = extract_inner_text(html, 'h1', 'hero-title')
    if lede:
        records.append({
            'archive': archive,
            'kind': 'hero-lede',
            'selector': 'h1.hero-title',
            'source_path': public_path,
            'expected_text': lede,
            'source_file': source_file,
        })
    else:
        print(f'warning: no h1.hero-title for {archive}', file=sys.stderr)

    # 2. hero-sub — <p class="hero-sub"> (wargov has hero-meta instead; skip if absent).
    sub = extract_inner_text(html, 'p', 'hero-sub')
    if sub:
        # Collapse interior whitespace runs — see _FooterParagraphFinder rationale
        # above. Source HTML wraps the lede paragraph across multiple lines for
        # readability; rendered text is one logical paragraph.
        sub = re.sub(r'\s+', ' ', sub)
        records.append({
            'archive': archive,
            'kind': 'hero-sub',
            'selector': 'p.hero-sub',
            'source_path': public_path,
            'expected_text': sub,
            'source_file': source_file,
        })

    # 3. license-footer — first <p> inside <footer> matching a jurisdiction marker.
    license_text = extract_license_footer(html, archive)
    if license_text:
        records.append({
            'archive': archive,
            'kind': 'license-footer',
            'selector': 'footer p',
            'source_path': public_path,
            'expected_text': license_text,
            'source_file': source_file,
        })
    else:
        print(f'warning: no license-footer text for {archive}', file=sys.stderr)

    # 4. card-title — first N from inline arch-data / archive-manifest JSON.
    for idx, title in enumerate(first_card_titles(html, CARD_TITLE_N)):
        records.append({
            'archive': archive,
            'kind': 'card-title',
            'selector': f'script#arch-data[{idx}].ti',
            'source_path': public_path,
            'expected_text': title,
            'source_file': source_file,
        })

    return records


# --- about.html semantic headings (faq-answer surrogate) -------------------

class _SectionHeadingFinder(HTMLParser):
    """Collect (heading-text, following-paragraph-text) pairs from <h2> + <p>.

    Used to harvest /about.html section content as the closest available
    surrogate for D-18's "FAQ accordion answers" — the current main has
    no FAQ accordion, only an About page with section headings and
    paragraphs. Per D-18, FAQ samples are extracted "where present"; this
    surrogate preserves the spirit (verbatim public-facing prose) while
    honouring the actual markup. If a future plan adds an FAQ accordion,
    the extractor can target it directly; in the meantime this provides
    coverage for the gate.
    """

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
            # Only capture the FIRST <p> after each <h2>.
            self._last_h2 = None

    def handle_data(self, data: str) -> None:
        if self._in_h2:
            self._h2_buf.append(data)
        elif self._in_p_after_h2:
            self._p_buf.append(data)


def extract_about_faq(n: int = 5) -> list[dict]:
    """Pull first N (h2-heading, paragraph) pairs from about.html as faq-answer samples."""
    path = REPO / 'about.html'
    if not path.exists():
        return []
    finder = _SectionHeadingFinder()
    try:
        finder.feed(path.read_text(encoding='utf-8'))
    except Exception as exc:  # pragma: no cover
        print(f'warning: about.html parse failed: {exc}', file=sys.stderr)
        return []
    out: list[dict] = []
    for idx, (heading, para) in enumerate(finder.entries[:n]):
        out.append({
            'archive': 'wargov',
            'kind': 'faq-answer',
            'selector': f'main h2#{idx} + p',
            'source_path': '/about.html',
            'expected_text': para,
            'source_file': 'about.html',
            # extra context (not in REQUIRED_FIELDS, but informational)
            'heading': heading,
        })
    return out


# --- CLI entry point -------------------------------------------------------

def build_all() -> list[dict]:
    """Walk every archive, accumulate every sample record."""
    records: list[dict] = []
    counts: dict[str, int] = {}
    for archive, rel_path, public_path in ARCHIVES_AND_PATHS:
        full_path = REPO / rel_path
        if not full_path.is_file():
            print(f'warning: missing {rel_path}', file=sys.stderr)
            continue
        archive_records = extract_for_archive(archive, full_path, public_path)
        records.extend(archive_records)
        counts[archive] = len(archive_records)
        print(f'[ok]    {archive}: {len(archive_records)} samples', file=sys.stderr)
    # FAQ surrogate from about.html (D-18 "where present" — best-effort).
    faq_records = extract_about_faq(n=5)
    records.extend(faq_records)
    if faq_records:
        print(f'[ok]    about/faq: {len(faq_records)} samples', file=sys.stderr)
    return records


def validate_schema(records: list[dict]) -> list[str]:
    """Return list of validation error strings (empty = valid)."""
    errors: list[str] = []
    if not isinstance(records, list):
        errors.append(f'top-level must be list, got {type(records).__name__}')
        return errors
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f'record {i}: not a dict')
            continue
        missing = REQUIRED_FIELDS - set(record.keys())
        if missing:
            errors.append(f'record {i} ({record.get("archive")}/{record.get("kind")}): missing fields {sorted(missing)}')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Extract the locked fidelity-sample list from current main HTML.',
    )
    parser.add_argument(
        '--stdout', action='store_true',
        help='Print the generated JSON to stdout instead of writing the file.',
    )
    parser.add_argument(
        '--check', action='store_true',
        help='Validate that tests/fidelity-samples.json exists and schema matches.',
    )
    args = parser.parse_args()

    if args.check:
        if not OUTPUT.exists():
            print(f'tests/fidelity-samples.json missing at {OUTPUT}', file=sys.stderr)
            return 1
        try:
            existing = json.loads(OUTPUT.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as exc:
            print(f'tests/fidelity-samples.json unreadable: {exc}', file=sys.stderr)
            return 1
        errors = validate_schema(existing)
        if errors:
            for err in errors:
                print(f'schema error: {err}', file=sys.stderr)
            return 1
        print(f'tests/fidelity-samples.json valid ({len(existing)} records).')
        return 0

    records = build_all()
    payload = json.dumps(records, ensure_ascii=False, indent=2) + '\n'
    if args.stdout:
        sys.stdout.write(payload)
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(payload, encoding='utf-8')
    print(f'Wrote {OUTPUT.relative_to(REPO)} — {len(records)} samples.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
