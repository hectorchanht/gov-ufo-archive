#!/usr/bin/env python3
"""Refresh the war.gov/UFO mirror manifest inside index.html.

Re-reads uap-release001.csv, re-checks what's locally available (with
git-tracking awareness — gitignored files are treated as remote), and
swaps the embedded `<script id="archive-manifest">` JSON in index.html
in-place. All HTML structure, CSS, and JS stay untouched.

Run after adding new entries to the CSV, or whenever new files land
in `slideshow/`, `bundles/Release_1/`, or `bundles/uapvideos/`.
"""
from __future__ import annotations
import csv, json, os, re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(REPO, 'index.html')
CSV   = os.path.join(REPO, 'uap-release001.csv')


import subprocess

def lsdir(rel_dir: str) -> set[str]:
    """Set of filenames *committed* under <repo>/<rel_dir>/.

    Git-tracking-aware so Download buttons on the deployed site only point
    at files that will actually be served — gitignored files always route
    through their source URL instead.
    """
    try:
        out = subprocess.run(
            ['git', '-C', REPO, 'ls-files', f'{rel_dir}/'],
            capture_output=True, text=True, check=True,
        ).stdout
        prefix = f'{rel_dir}/'
        return {ln[len(prefix):] for ln in out.splitlines() if ln.startswith(prefix)}
    except (subprocess.CalledProcessError, FileNotFoundError):
        # No git yet — fall back to disk so the page builds at all.
        p = os.path.join(REPO, rel_dir)
        return set(os.listdir(p)) if os.path.isdir(p) else set()


def basename(url: str) -> str:
    return url.rstrip('/').rsplit('/', 1)[-1].split('?')[0]


# === Build the manifest ===
slideshow_files = sorted(lsdir('slideshow'))
pdf_files       = sorted(lsdir('bundles/Release_1'))
video_files     = sorted(lsdir('bundles/uapvideos'))

slide_l = {f.lower(): f for f in slideshow_files}
pdf_l   = {f.lower(): f for f in pdf_files}

rows: list[dict] = []
with open(CSV, encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        clean = {k.strip(): (v.strip() if v else '') for k, v in r.items() if k and k.strip()}
        if not clean.get('Type'):
            continue
        rows.append(clean)

for r in rows:
    url = r.get('PDF | Image Link', '')
    bn = basename(url).lower()
    if bn in pdf_l:
        r['local'] = 'bundles/Release_1/' + pdf_l[bn]
    elif bn in slide_l:
        r['local'] = 'slideshow/' + slide_l[bn]
    else:
        r['local'] = ''

manifest = {
    'rows': rows,
    'slideshow_files': slideshow_files,
    'pdf_files': pdf_files,
    'video_files': video_files,
}
manifest_json = json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))
manifest_json = manifest_json.replace('</script', '<\\/script')

# === Splice into index.html ===
src = open(INDEX, encoding='utf-8').read()
pattern = re.compile(
    r'(<script id="archive-manifest" type="application/json">)(.*?)(</script>)',
    re.S,
)
m = pattern.search(src)
if not m:
    raise SystemExit('index.html: <script id="archive-manifest"> block not found')

new_src = src[:m.start(2)] + manifest_json + src[m.end(2):]
open(INDEX, 'w', encoding='utf-8').write(new_src)

# === Summary ===
local_count = sum(1 for r in rows if r.get('local'))
print(f'index.html refreshed')
print(f'  CSV rows:        {len(rows)}')
print(f'  slideshow files: {len(slideshow_files)}')
print(f'  Release_1 files: {len(pdf_files)}  ({local_count} CSV rows matched)')
print(f'  DVIDS videos:    {len(video_files)}')
