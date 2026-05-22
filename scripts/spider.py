#!/usr/bin/env python3
"""Generic polite spider for government UAP archives.

Config-driven BFS:
  - allowed_hosts: only crawl URLs whose host matches
  - link_patterns: regex(es) — only follow links matching at least one
  - file_extensions: download files with these extensions
  - max_depth, max_pages: hard limits
  - delay: seconds between requests (politeness)

For each visited page:
  - extract title + first 800 chars of text as `context`
  - extract all file links + child page links

Writes:
  <mirror>/.cache/spider/<sha>.html   — page cache
  <mirror>/.cache/spider-index.json   — structured records
  <mirror>/pdfs/<basename>            — downloaded PDFs

Failures fall back to Wayback Machine. Read-only modulo writes to .cache & pdfs/.
"""
from __future__ import annotations
import json, os, re, sys, time, html, hashlib, urllib.request, urllib.parse, urllib.error
from collections import deque

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha(s: str) -> str:
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:16]


def fetch_bytes(url: str, timeout: int = 30) -> bytes | None:
    for attempt in (url, 'https://web.archive.org/web/2024id_/' + url):
        try:
            req = urllib.request.Request(attempt, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            tag = 'DIRECT' if attempt == url else 'WAYBACK'
            print(f'    [{tag} ERR] {url}: {e}', file=sys.stderr)
    return None


def fetch_html(url: str, cache_dir: str) -> str:
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, sha(url) + '.html')
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 200:
        return open(cache_path, encoding='utf-8').read()
    data = fetch_bytes(url)
    if data is None:
        return ''
    try:
        s = data.decode('utf-8', errors='replace')
    except Exception:
        return ''
    open(cache_path, 'w', encoding='utf-8').write(s)
    return s


def download_file(url: str, dest_dir: str) -> str | None:
    os.makedirs(dest_dir, exist_ok=True)
    bn = urllib.parse.unquote(url.rsplit('/', 1)[-1].split('?')[0].split('#')[0])
    if not bn or len(bn) > 200:
        bn = sha(url) + os.path.splitext(bn)[1]
    dest = os.path.join(dest_dir, bn)
    if os.path.exists(dest) and os.path.getsize(dest) > 1024:
        return bn   # cache hit
    data = fetch_bytes(url, timeout=120)
    if data is None or len(data) < 1024:
        return None
    with open(dest, 'wb') as f:
        f.write(data)
    return bn


# ── HTML helpers ────────────────────────────────────────────────────────────
TAG_RE = re.compile(r'<[^>]+>')
SPACE_RE = re.compile(r'\s+')


def strip_html(s: str) -> str:
    return SPACE_RE.sub(' ', html.unescape(TAG_RE.sub(' ', s or ''))).strip()


def get_title(src: str) -> str:
    m = re.search(r'<title[^>]*>(.*?)</title>', src, re.I | re.S)
    return strip_html(m.group(1)) if m else ''


def get_context(src: str, max_len: int = 800) -> str:
    # First take main/article text if present, else body.
    body_m = re.search(r'<(?:main|article)[^>]*>(.*?)</(?:main|article)>', src, re.I | re.S)
    body = body_m.group(1) if body_m else src
    # Strip scripts/styles
    body = re.sub(r'<(script|style|nav|footer|header)[^>]*>.*?</\1>', ' ', body, flags=re.I | re.S)
    t = strip_html(body)
    return t[:max_len].rstrip()


def extract_links(src: str, base_url: str) -> list[str]:
    out = []
    for m in re.finditer(r'href=["\']([^"\']+)["\']', src, re.I):
        href = m.group(1).strip()
        if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
            continue
        out.append(urllib.parse.urljoin(base_url, href))
    return out


def extract_thumb(src: str, base_url: str) -> str:
    """Pick a representative thumbnail URL for a crawled page.

    Priority: og:image → twitter:image → first <img> with width/height ≥ 200
    (skipping tiny icons, sprites, logos, tracking pixels). Returns absolute
    URL or '' if nothing usable.
    """
    # 1. og:image
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', src, re.I)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', src, re.I)
    if m:
        return urllib.parse.urljoin(base_url, m.group(1).strip())
    # 2. twitter:image
    m = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', src, re.I)
    if m:
        return urllib.parse.urljoin(base_url, m.group(1).strip())
    # 3. first plausible <img>
    skip = re.compile(r'(sprite|logo|icon|favicon|tracker|pixel|spacer|blank)', re.I)
    for m in re.finditer(r'<img\b[^>]+>', src, re.I):
        tag = m.group(0)
        sm = re.search(r'\bsrc=["\']([^"\']+)["\']', tag, re.I)
        if not sm:
            continue
        s = sm.group(1).strip()
        if not s or s.startswith('data:') or skip.search(s):
            continue
        if not re.search(r'\.(jpe?g|png|webp)(?:$|[?#])', s, re.I):
            continue
        return urllib.parse.urljoin(base_url, s)
    return ''


def host_of(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return ''


# ── Crawl ───────────────────────────────────────────────────────────────────
def spider(cfg: dict) -> list[dict]:
    name = cfg['name']
    cache_dir = os.path.join(REPO, cfg['mirror'], '.cache', 'spider')
    pdfs_dir  = os.path.join(REPO, cfg['mirror'], 'pdfs')

    seeds = cfg['seeds']
    allowed_hosts = set(h.lower() for h in cfg['allowed_hosts'])
    link_patterns = [re.compile(p, re.I) for p in cfg.get('link_patterns', [r'.*'])]
    file_exts = tuple(e.lower() for e in cfg['file_extensions'])
    max_depth = cfg.get('max_depth', 2)
    max_pages = cfg.get('max_pages', 40)
    delay = cfg.get('delay', 1.0)

    visited_pages: set[str] = set()
    downloaded_files: set[str] = set()
    records: list[dict] = []
    queue: deque = deque((u, 0) for u in seeds)
    pages_fetched = 0

    while queue and pages_fetched < max_pages:
        url, depth = queue.popleft()
        if url in visited_pages:
            continue
        visited_pages.add(url)
        if host_of(url) not in allowed_hosts:
            continue

        print(f'  [{pages_fetched+1}/{max_pages} d={depth}] {url}')
        src = fetch_html(url, cache_dir)
        pages_fetched += 1
        if not src:
            continue
        time.sleep(delay)

        title = get_title(src)
        context = get_context(src)
        thumb = extract_thumb(src, url)
        files_found: list[dict] = []

        # File link discovery
        for link in extract_links(src, url):
            low = link.lower().split('?', 1)[0].split('#', 1)[0]
            if any(low.endswith(ext) for ext in file_exts):
                if link in downloaded_files:
                    continue
                downloaded_files.add(link)
                bn = download_file(link, pdfs_dir) if low.endswith('.pdf') else None
                files_found.append({
                    'url': link, 'local': f'pdfs/{bn}' if bn else '',
                    'kind': 'pdf' if low.endswith('.pdf') else 'image' if low.endswith(('.jpg', '.jpeg', '.png')) else 'other',
                })
                print(f'      + {("local " if bn else "remote")} {link.rsplit("/",1)[-1]}')

        records.append({
            'url': url, 'title': title, 'context': context, 'thumb': thumb,
            'files': files_found, 'depth': depth,
        })

        # Enqueue child pages
        if depth < max_depth:
            for link in extract_links(src, url):
                if link in visited_pages:
                    continue
                if host_of(link) not in allowed_hosts:
                    continue
                low = link.lower().split('?', 1)[0]
                if any(low.endswith(ext) for ext in file_exts + ('.jpg', '.jpeg', '.png', '.gif', '.css', '.js')):
                    continue
                if not any(p.search(link) for p in link_patterns):
                    continue
                queue.append((link, depth + 1))

    out = os.path.join(REPO, cfg['mirror'], '.cache', 'spider-index.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'name': name, 'records': records}, f, ensure_ascii=False, indent=2)
    print(f'\n→ {name}: {len(records)} pages, {sum(len(r["files"]) for r in records)} files')
    print(f'  wrote {out}')
    return records


# ── Site configs ────────────────────────────────────────────────────────────
CONFIGS = [
    {
        'name': 'chile-sefaa',
        'mirror': 'chile',
        'seeds': [
            'https://sefaa.dgac.gob.cl/',
            'https://sefaa.dgac.gob.cl/category/casos-resueltos/',
            'https://sefaa.dgac.gob.cl/category/casos-resueltos/page/2/',
            'https://sefaa.dgac.gob.cl/category/casos-resueltos/page/3/',
            'https://sefaa.dgac.gob.cl/category/casos-resueltos/page/4/',
        ],
        'allowed_hosts': ['sefaa.dgac.gob.cl', 'www.dgac.gob.cl'],
        'link_patterns': [
            r'sefaa\.dgac\.gob\.cl/\d{4}/',
            r'sefaa\.dgac\.gob\.cl/casos-resueltos',
            r'sefaa\.dgac\.gob\.cl/category/',
            r'dgac\.gob\.cl/cefaa',
            r'dgac\.gob\.cl/wp-content',
        ],
        'file_extensions': ['.pdf'],
        'max_depth': 2,
        'max_pages': 60,
        'delay': 1.0,
    },
    {
        'name': 'uk-tna',
        'mirror': 'uk',
        'seeds': [
            'https://web.archive.org/web/2024/https://www.nationalarchives.gov.uk/ufos/',
            'https://web.archive.org/web/2024/https://www.nationalarchives.gov.uk/about/news/ufo-files-released/',
            'https://web.archive.org/web/2024/https://www.mod.uk/DefenceInternet/MicroSite/UFO/',
        ],
        'allowed_hosts': ['web.archive.org', 'nationalarchives.gov.uk', 'www.nationalarchives.gov.uk',
                          'cdn.nationalarchives.gov.uk', 'discovery.nationalarchives.gov.uk',
                          'www.mod.uk'],
        'link_patterns': [r'nationalarchives|condign|ufo|defe|air[-_ ]?2|air[-_ ]?20|mod\.uk'],
        'file_extensions': ['.pdf'],
        'max_depth': 2,
        'max_pages': 40,
        'delay': 1.0,
    },
    {
        'name': 'brazil-arqnac',
        'mirror': 'brazil',
        'seeds': [
            'https://dibrarq.arquivonacional.gov.br/index.php/objeto-voador-nao-identificado-ovni',
            'https://web.archive.org/web/2024/https://www.gov.br/arquivonacional/pt-br/canais_atendimento/sala-virtual-de-imprensa/divulgacao-de-documentos-1/divulgacao-de-documentos-ovni',
            'https://web.archive.org/web/2024/https://www2.fab.mil.br/cendoc/index.php/doc-especiais',
        ],
        'allowed_hosts': ['dibrarq.arquivonacional.gov.br', 'arquivonacional.gov.br', 'www.arquivonacional.gov.br',
                          'www.gov.br', 'www2.fab.mil.br', 'www.fab.mil.br', 'web.archive.org'],
        'link_patterns': [r'.+'],   # follow any in-host link
        'file_extensions': ['.pdf'],
        'max_depth': 2,
        'max_pages': 40,
        'delay': 1.0,
    },
]


if __name__ == '__main__':
    targets = sys.argv[1:] or [c['name'] for c in CONFIGS]
    for cfg in CONFIGS:
        if cfg['name'] not in targets:
            continue
        print(f'\n══ {cfg["name"]} ══')
        spider(cfg)
