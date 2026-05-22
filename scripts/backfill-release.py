#!/usr/bin/env python3
"""Backfill missing PDF / video assets into GitHub Releases.

Walks every mirror's arch-data, finds direct file URLs (.pdf/.mp4/etc.),
checks against current pdfs-v1 / videos-v1 release assets, downloads
anything missing to a tmp dir, then prints the gh-release-upload command
the caller runs.

Also emits release-manifest.json — basename → release-download URL — which
build scripts read to swap u: to release URL when basename matches.

Run:
    python3 scripts/backfill-release.py [--upload]
"""
from __future__ import annotations
import json, os, re, sys, subprocess, urllib.request, urllib.parse
from urllib.parse import urlparse, unquote

REPO    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP     = '/tmp/backfill-release'
os.makedirs(TMP, exist_ok=True)
PDF_TAG = 'pdfs-v1'
VID_TAG = 'videos-v1'
RELEASE_BASE = 'https://github.com/hectorchanht/war-gov-ufo-release/releases/download'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

MIRRORS = ['aaro','nasa','nara','geipan','uk','brazil','chile',
           'nz','canada','argentina','uruguay','peru','spain','italy']


def basename(url: str) -> str:
    return unquote(urlparse(url).path.rsplit('/',1)[-1].split('?',1)[0].split('#',1)[0])


def get_release_assets(tag: str) -> set[str]:
    try:
        out = subprocess.run(['gh','release','view',tag,'--json','assets','-q','.assets[].name'],
                             capture_output=True, text=True, check=True).stdout
        return set(out.splitlines())
    except subprocess.CalledProcessError:
        return set()


def collect_file_urls() -> tuple[dict, dict]:
    """Returns (pdf_urls, vid_urls) keyed by basename."""
    pdfs, vids = {}, {}
    for m in MIRRORS:
        path = os.path.join(REPO, m, 'index.html')
        if not os.path.exists(path): continue
        s = open(path, encoding='utf-8').read()
        match = re.search(r'<script[^>]+id="arch-data"[^>]*>([\s\S]*?)</script>', s)
        if not match: continue
        try: data = json.loads(match.group(1))
        except: continue
        for a in data.get('assets',[]) + data.get('cases',[]):
            u = a.get('u','') or a.get('url','')
            if not u: continue
            low = u.lower().split('?',1)[0].split('#',1)[0]
            bn = basename(u)
            if not bn or len(bn) > 200: continue
            if low.endswith('.pdf'): pdfs[bn] = u
            elif low.endswith(('.mp4','.webm','.mov')): vids[bn] = u
    return pdfs, vids


def download(url: str, dest: str, timeout: int = 30) -> bool:
    if os.path.exists(dest) and os.path.getsize(dest) > 1024: return True
    # Mark as "tried but failed" so re-runs skip immediately.
    fail_marker = dest + '.fail'
    if os.path.exists(fail_marker): return False
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
    except Exception as e:
        print(f'  [FAIL] {basename(url)}: {e}', flush=True)
        open(fail_marker, 'w').write(str(e))
        return False
    if len(data) < 1024:
        open(fail_marker, 'w').write('too-small')
        return False
    with open(dest, 'wb') as f: f.write(data)
    print(f'  [OK]   {basename(url)} ({len(data)//1024} KB)', flush=True)
    return True


def main(upload: bool = False):
    pdf_in_release = get_release_assets(PDF_TAG)
    vid_in_release = get_release_assets(VID_TAG)
    print(f'Currently in {PDF_TAG}: {len(pdf_in_release)}  in {VID_TAG}: {len(vid_in_release)}')

    pdfs, vids = collect_file_urls()
    pdf_missing = {bn:u for bn,u in pdfs.items() if bn not in pdf_in_release}
    vid_missing = {bn:u for bn,u in vids.items() if bn not in vid_in_release}
    print(f'PDFs missing from release: {len(pdf_missing)}')
    print(f'Videos missing from release: {len(vid_missing)}')

    downloaded_pdfs, downloaded_vids = [], []
    for bn, url in pdf_missing.items():
        dest = os.path.join(TMP, bn)
        print(f'→ PDF {bn} ← {url[:80]}')
        if download(url, dest): downloaded_pdfs.append(dest)
    for bn, url in vid_missing.items():
        dest = os.path.join(TMP, bn)
        print(f'→ VID {bn} ← {url[:80]}')
        if download(url, dest, timeout=600): downloaded_vids.append(dest)

    print(f'\nDownloaded: {len(downloaded_pdfs)} PDFs + {len(downloaded_vids)} videos to {TMP}')

    if upload and downloaded_pdfs:
        print('Uploading PDFs...')
        # Upload in batches of 25 to avoid gh argv limits
        for i in range(0, len(downloaded_pdfs), 25):
            batch = downloaded_pdfs[i:i+25]
            subprocess.run(['gh','release','upload',PDF_TAG,'--clobber',*batch], check=False)
    if upload and downloaded_vids:
        print('Uploading videos...')
        for i in range(0, len(downloaded_vids), 10):
            batch = downloaded_vids[i:i+10]
            subprocess.run(['gh','release','upload',VID_TAG,'--clobber',*batch], check=False)

    # Refresh release lists and write manifest
    pdf_in_release = get_release_assets(PDF_TAG) | {os.path.basename(p) for p in downloaded_pdfs}
    vid_in_release = get_release_assets(VID_TAG) | {os.path.basename(p) for p in downloaded_vids}

    manifest = {
        'pdfs': {bn: f'{RELEASE_BASE}/{PDF_TAG}/{urllib.parse.quote(bn)}' for bn in sorted(pdf_in_release)},
        'videos': {bn: f'{RELEASE_BASE}/{VID_TAG}/{urllib.parse.quote(bn)}' for bn in sorted(vid_in_release)},
    }
    mpath = os.path.join(REPO, 'release-manifest.json')
    with open(mpath, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f'Wrote {mpath} — {len(manifest["pdfs"])} PDFs + {len(manifest["videos"])} videos mapped')


if __name__ == '__main__':
    main(upload='--upload' in sys.argv)
