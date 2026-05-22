#!/usr/bin/env python3
"""Build evidence map (videos, PDFs, images + captions) from parsed page data.

Input:  aaro/.cache/parsed.json   (from parse-aaro.py)
Output: aaro/.cache/evidence.json (consumed by build-aaro.py)
"""
import os, re, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AARO = os.path.join(ROOT, 'aaro')
PAGES = os.path.join(AARO, 'pages')
CACHE = os.path.join(AARO, '.cache')
os.makedirs(CACHE, exist_ok=True)

evidence = {'videos': [], 'pdfs': [], 'images': []}

# === Official UAP Imagery: video map ===
src = open(os.path.join(PAGES, 'official-uap-imagery.html')).read()
# Find all video sources (cloudfront) — these match DOD_NNN files
dod_urls = sorted(set(re.findall(r'(https://d34w7g4gy10iej\.cloudfront\.net/video/\d+/DOD_\d+/DOD_\d+(?:-[\w-]+)?\.mp4)', src)))
print('cloudfront video URLs:', len(dod_urls))

# Match DVIDS video links with titles
dvids_titles = {}
for m in re.finditer(r'<a[^>]*href="[^"]*video/(\d+)[^"]*"[^>]*>([^<]{5,200})</a>', src):
    dvids_id = m.group(1)
    title = m.group(2).strip().replace('&quot;','"').replace('&amp;','&')
    if dvids_id not in dvids_titles or len(title) > len(dvids_titles[dvids_id]):
        dvids_titles[dvids_id] = title
print('dvids titles:', len(dvids_titles))

# In the page, video iframe/embed link and the surrounding <h3> or caption gives context
# Try to find h3/h4/p captions near each video. Use a broader regex to extract list-style content
# Find each video container - typically a div with class*="video-container" or "videoItem"
# Build by iterating page text in order
# Each cloudfront video URL appears near its descriptive heading
# Best heuristic: split by cloudfront URLs and grab nearest title text after each
positions = []
for m in re.finditer(r'(DOD_\d+)', src):
    positions.append((m.start(), m.group(1)))
# Find <a href="...video/N"...>Title</a> nearest each DOD
title_at = []  # (pos, dvids_id, title)
for m in re.finditer(r'<a[^>]*href="[^"]*video/(\d+)[^"]*"[^>]*>([^<]{5,200})</a>', src):
    title_at.append((m.start(), m.group(1), m.group(2).strip().replace('&quot;','"').replace('&amp;','&')))

# For each DOD video, find closest preceding title-at link
dod_to_title = {}
for pos, dod in positions:
    closest = None
    for tpos, did, ttl in title_at:
        if tpos < pos:
            closest = (tpos, did, ttl)
    if closest:
        if dod not in dod_to_title:
            dod_to_title[dod] = closest

# Group DOD by URL
for url in dod_urls:
    m = re.search(r'(DOD_\d+)', url)
    if not m: continue
    dod = m.group(1)
    info = dod_to_title.get(dod, (None, None, dod))
    evidence['videos'].append({
        'dod_id': dod,
        'url': url,
        'filename': url.rsplit('/',1)[-1],
        'dvids_id': info[1],
        'title': info[2] or dod,
    })

# === Resources page: aaro.mil image URLs ===
# Also UAP Reporting Trends has chart images
for slug in ['uap-reporting-trends','uap-case-resolution-reports','uap-records']:
    p = os.path.join(PAGES, f'{slug}.html')
    if not os.path.exists(p): continue
    s = open(p).read()
    for m in re.finditer(r'src="(?:/web/\d+[a-z_]*/)?([^"\s]+)"', s):
        u = m.group(1)
        if 'aaro.mil' in u and any(u.lower().endswith(e) for e in ('.png','.jpg','.jpeg','.gif','.svg')):
            evidence['images'].append({'src_page': slug, 'url': u})

# === All PDFs ===
all_parsed = json.load(open(os.path.join(CACHE, 'parsed.json')))
evidence['pdfs'] = [{'url': u} for u in all_parsed['all_pdfs']]
# All images
seen = set(i['url'] for i in evidence['images'])
for u in all_parsed['all_images']:
    if u not in seen:
        evidence['images'].append({'src_page': None, 'url': u})
        seen.add(u)

json.dump(evidence, open(os.path.join(CACHE, 'evidence.json'),'w'), indent=2)
print('videos:', len(evidence['videos']))
print('pdfs:', len(evidence['pdfs']))
print('images:', len(evidence['images']))
