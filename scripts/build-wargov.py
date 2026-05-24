#!/usr/bin/env python3
"""Refresh the war.gov/UFO archive manifest embedded in index.html.

Re-reads uap-data.csv (the combined Release 01 + Release 02 manifest served
by war.gov), re-checks what's locally available (with git-tracking awareness —
gitignored files are treated as remote), and swaps the embedded
`<script id="archive-manifest">` JSON in index.html in-place. All HTML
structure, CSS, and JS stay untouched.

Run after adding new entries to the CSV, or whenever new files land in
`slideshow/`, `slideshow-2/`, `bundles/Release_1/`, `bundles/uapvideos/`,
`bundles/release_02_document_bundle/`, or `bundles/uap052226/`.

Notes:
  * The legacy uap-release001.csv is kept as-is in the repo (CLAUDE.md §11).
  * The DVIDS → DOD record-ID mapping for Release 02 videos lives in
    scripts/dvids2dod-r02.json (resolved once by hitting dvidshub.net).
"""
from __future__ import annotations
import csv, json, os, re, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(REPO, 'index.html')

# Prefer the combined manifest (R01 + R02). Fall back to legacy R01-only CSV
# if uap-data.csv has not been synced yet (clean clone, first-run scenario).
CSV_COMBINED = os.path.join(REPO, 'uap-data.csv')
CSV_LEGACY   = os.path.join(REPO, 'uap-release001.csv')
CSV          = CSV_COMBINED if os.path.exists(CSV_COMBINED) else CSV_LEGACY

LOCAL_PREFIX = ''   # index.html is at repo root


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
        p = os.path.join(REPO, rel_dir)
        return set(os.listdir(p)) if os.path.isdir(p) else set()


def lsdir_present(rel_dir: str) -> set[str]:
    """Filenames actually present on disk (used to build the full expected
    catalogue, regardless of whether the file is git-tracked).
    """
    p = os.path.join(REPO, rel_dir)
    return set(os.listdir(p)) if os.path.isdir(p) else set()


def basename(url: str) -> str:
    return url.rstrip('/').rsplit('/', 1)[-1].split('?')[0]


# ---------------------------------------------------------------------------
# Expected DVIDS / DOD video catalogue — Release 01 + Release 02
# ---------------------------------------------------------------------------

# Release 01: original 28 DVIDS bundle videos shipped inside uapvideos.zip.
EXPECTED_VIDEOS_R01 = [
    f"DOD_{n}.mp4" for n in (
        111688723, 111688762, 111688775, 111688809, 111688816, 111688825,
        111688954, 111688964, 111688970, 111688997, 111689005, 111689011,
        111689022, 111689030, 111689044, 111689051, 111689057, 111689082,
        111689083, 111689090, 111689115, 111689123, 111689133, 111689142,
        111689167, 111689168, 111689232, 111689759,
    )
]

# Release 02: 57 mp4 files (51 video + 7 audio-served-as-mp4) inside
# uap052226.zip. The bundle ships them as `video_2605_DOD_<id>_DOD_<id>.mp4`;
# they're renamed to canonical `DOD_<id>.mp4` on extract.
def _load_dvids_map(name: str) -> dict[str, str]:
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    if not os.path.exists(p):
        return {}
    return json.load(open(p))

def _load_r02_dod_ids() -> list[str]:
    m = _load_dvids_map('dvids2dod-r02.json')
    return sorted({f"DOD_{v}.mp4" for v in m.values()})

EXPECTED_VIDEOS_R02 = _load_r02_dod_ids()

# Combined DVIDS Video ID → DOD record-id map (R01 + R02). Used to fill
# in the playable URL for catalog VID rows that ship only a DVIDS ID.
DVIDS_TO_DOD = {**_load_dvids_map('dvids2dod-r01.json'),
                **_load_dvids_map('dvids2dod-r02.json')}

# ---------------------------------------------------------------------------
# Build the manifest
# ---------------------------------------------------------------------------

slideshow_r01 = sorted(lsdir('slideshow'))
slideshow_r02 = sorted(lsdir('slideshow-2'))
slideshow_files = sorted(set(slideshow_r01) | set(slideshow_r02))

pdf_files_r01 = sorted(lsdir('bundles/Release_1'))
pdf_files_r02 = sorted(lsdir('bundles/release_02_document_bundle'))
pdf_files = sorted(set(pdf_files_r01) | set(pdf_files_r02))

tracked_videos_r01 = lsdir('bundles/uapvideos')
tracked_videos_r02 = lsdir('bundles/uap052226')
tracked_videos = tracked_videos_r01 | tracked_videos_r02

video_files_r01 = sorted(set(EXPECTED_VIDEOS_R01) | tracked_videos_r01)
video_files_r02 = sorted(set(EXPECTED_VIDEOS_R02) | tracked_videos_r02)
video_files = sorted(set(video_files_r01) | set(video_files_r02))

slide_l  = {f.lower(): ('slideshow/'   + f) for f in slideshow_r01}
slide_l.update({f.lower(): ('slideshow-2/' + f) for f in slideshow_r02})
pdf_l    = {f.lower(): ('bundles/Release_1/' + f) for f in pdf_files_r01}
pdf_l.update({f.lower(): ('bundles/release_02_document_bundle/' + f) for f in pdf_files_r02})

# CSV rows
rows: list[dict] = []
with open(CSV, encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        clean = {k.strip(): (v.strip() if v else '') for k, v in r.items() if k and k.strip()}
        if not clean.get('Type'):
            continue
        # Strip blank padding columns
        clean = {k: v for k, v in clean.items() if k}
        rows.append(clean)

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _release_manifest import load_manifest as _load_release_manifest
_rel_man = _load_release_manifest()
_rel_pdfs = _rel_man.get('pdfs', {})
_rel_vids = _rel_man.get('videos', {})

for r in rows:
    url = r.get('PDF | Image Link', '')
    # Catalog VID rows (PR050, PR051, …) ship only a DVIDS Video ID; resolve
    # it to the release URL of the DOD_*.mp4 so the card has a playable link.
    if not url and r.get('Type', '').strip() == 'VID':
        d = (r.get('DVIDS Video ID') or '').strip()
        dod = DVIDS_TO_DOD.get(d)
        if dod:
            vid_bn = f'DOD_{dod}.mp4'
            if vid_bn in _rel_vids:
                url = _rel_vids[vid_bn]
                r['PDF | Image Link'] = url
    bn_l = basename(url).lower()
    bn   = basename(url)
    # Local file mapping (bundles/slideshow) takes precedence for offline.
    if bn_l in pdf_l:
        r['local'] = LOCAL_PREFIX + pdf_l[bn_l]
    elif bn_l in slide_l:
        r['local'] = LOCAL_PREFIX + slide_l[bn_l]
    else:
        r['local'] = ''
    # If the file is in a GitHub Release tag, rewrite primary URL to the
    # release download so deployed pages always have a working link.
    if bn in _rel_pdfs:
        r['PDF | Image Link'] = _rel_pdfs[bn]
    elif bn in _rel_vids:
        r['PDF | Image Link'] = _rel_vids[bn]

manifest = {
    'rows': rows,
    'slideshow_files': slideshow_files,
    'slideshow_files_r01': slideshow_r01,
    'slideshow_files_r02': slideshow_r02,
    'pdf_files': pdf_files,
    'pdf_files_r01': pdf_files_r01,
    'pdf_files_r02': pdf_files_r02,
    'video_files': video_files,
    'video_files_r01': video_files_r01,
    'video_files_r02': video_files_r02,
    'tracked_videos': sorted(tracked_videos),
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
r1 = sum(1 for r in rows if r.get('Release Date','').strip() == '5/8/26')
r2 = sum(1 for r in rows if r.get('Release Date','').strip() == '5/22/26')
local_count = sum(1 for r in rows if r.get('local'))
print(f'index.html refreshed  (CSV: {os.path.basename(CSV)})')
print(f'  CSV rows:        {len(rows)}   (R01: {r1}, R02: {r2})')
print(f'  slideshow files: {len(slideshow_files)}  (R01: {len(slideshow_r01)}, R02: {len(slideshow_r02)})')
print(f'  PDF files:       {len(pdf_files)}  (R01: {len(pdf_files_r01)}, R02: {len(pdf_files_r02)})   ({local_count} CSV rows matched local)')
print(f'  DVIDS videos:    {len(video_files)}  (R01: {len(video_files_r01)}, R02: {len(video_files_r02)})')
