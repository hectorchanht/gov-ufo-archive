#!/usr/bin/env python3
"""Parse the downloaded aaro.mil page snapshots into a clean JSON manifest.

Output: aaro-mirror/.cache/parsed.json
Idempotent — safe to re-run anytime new page snapshots arrive.
"""
import os, re, json, html, urllib.parse
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AARO = os.path.join(ROOT, 'aaro-mirror')
PAGES_DIR = os.path.join(AARO, 'pages')
CACHE_DIR = os.path.join(AARO, '.cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def wb_strip(u):
    m = re.match(r'^https?://web\.archive\.org/web/\d+[a-z_]*/(.+)$', u)
    if m: return m.group(1)
    m = re.match(r'^/?web/\d+[a-z_]*/(https?://.+)$', u)
    if m: return m.group(1)
    return u

def extract_main(html_src):
    """Find the <div id="content" role="main"> ... </div> region. Handle nested divs."""
    # Find start of content
    m = re.search(r'<div\s+id="content"\s+role="main"[^>]*>', html_src)
    if not m:
        m = re.search(r'<main\b[^>]*>', html_src)
        if not m: return ''
        end_tag = 'main'
    else:
        end_tag = 'div'
    start = m.end()
    # Walk forward counting nested div/main
    depth = 1
    pos = start
    pattern = re.compile(rf'<(/?)({end_tag})\b[^>]*>', re.I)
    while depth > 0:
        m2 = pattern.search(html_src, pos)
        if not m2: break
        if m2.group(1) == '/':
            depth -= 1
            if depth == 0:
                return html_src[start:m2.start()]
        else:
            depth += 1
        pos = m2.end()
    return html_src[start:]

class MainExtractor(HTMLParser):
    """Lightweight extractor — captures images, links, and clean paragraphed text."""
    SKIP_TAGS = {'script','style','noscript','svg'}
    SKIP_CLASSES = ('wb-','wm-','wayback','toolbar')
    def __init__(self):
        super().__init__()
        self.text_chunks = []
        self.headings = []     # list of (level, text)
        self.images = []
        self.links = []
        self.tag_stack = []
        self.skip_depth = 0
        self.cur_link = None
        self.cur_link_text = []
        self.cur_h = None
        self.last_was_block = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth: return
        cls = a.get('class','')
        if any(cls.startswith(p) for p in self.SKIP_CLASSES):
            self.skip_depth += 1; return
        self.tag_stack.append(tag)
        if tag in ('h1','h2','h3','h4'):
            self.cur_h = (tag, [])
        if tag == 'a' and 'href' in a:
            self.cur_link = wb_strip(a['href'])
            self.cur_link_text = []
        if tag == 'img' and 'src' in a:
            src = wb_strip(a['src'])
            if src.startswith('/'): src = urllib.parse.urljoin('https://www.aaro.mil/', src)
            self.images.append({'src': src, 'alt': a.get('alt',''), 'title': a.get('title','')})
        if tag in ('p','br','li','div','tr','table','section','article','h1','h2','h3','h4','blockquote'):
            if self.text_chunks and not self.text_chunks[-1].endswith('\n'):
                self.text_chunks.append('\n')
            if tag in ('p','div','section','article','table','blockquote') and self.text_chunks and not self.text_chunks[-1].endswith('\n\n'):
                self.text_chunks.append('\n')
    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            self.skip_depth = max(0,self.skip_depth-1); return
        if self.skip_depth:
            # might be closing a skip-class div
            self.skip_depth = max(0,self.skip_depth-1); return
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
        if tag in ('h1','h2','h3','h4') and self.cur_h:
            t = ''.join(self.cur_h[1]).strip()
            if t: self.headings.append({'level':self.cur_h[0],'text':t})
            self.cur_h = None
        if tag == 'a' and self.cur_link is not None:
            txt = ''.join(self.cur_link_text).strip()
            self.links.append({'href':self.cur_link,'label':txt[:200]})
            self.cur_link = None; self.cur_link_text = []
        if tag in ('p','div','li','tr','table','section','article','h1','h2','h3','h4','blockquote'):
            self.text_chunks.append('\n')
    def handle_data(self, data):
        if self.skip_depth: return
        self.text_chunks.append(data)
        if self.cur_h: self.cur_h[1].append(data)
        if self.cur_link is not None: self.cur_link_text.append(data)

def categorize(text):
    """Clean up whitespace, return paragraphs."""
    # Collapse runs of whitespace inside lines
    lines = text.split('\n')
    out = []
    for l in lines:
        l = re.sub(r'[\t ]+',' ', l).strip()
        out.append(l)
    # Collapse runs of empty lines
    result = []
    blank = 0
    for l in out:
        if not l:
            blank += 1
            if blank <= 1: result.append('')
        else:
            blank = 0
            result.append(l)
    return '\n'.join(result).strip()

results = {}
all_pdfs = set()
all_images = set()

for fn in sorted(os.listdir(PAGES_DIR)):
    if not fn.endswith('.html'): continue
    slug = fn[:-5]
    src = open(os.path.join(PAGES_DIR, fn), encoding='utf-8', errors='replace').read()
    main_html = extract_main(src)
    if not main_html:
        # fallback: strip head and use body
        m = re.search(r'<body[^>]*>(.*)</body>', src, re.S)
        main_html = m.group(1) if m else src

    title_m = re.search(r'<title[^>]*>([^<]+)</title>', src)
    title = title_m.group(1).strip() if title_m else slug

    ex = MainExtractor()
    try: ex.feed(main_html)
    except Exception as e: print(f'  parse err {slug}: {e}')

    raw_text = ''.join(ex.text_chunks)
    clean_text = categorize(raw_text)

    # Aggregate assets
    page_links = []
    for L in ex.links:
        href = L['href']
        if not href: continue
        if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'): continue
        if not href.startswith('http'):
            href = urllib.parse.urljoin('https://www.aaro.mil/', href)
        L['href'] = href
        page_links.append(L)
        if 'aaro.mil' in href:
            low = href.lower()
            if low.endswith('.pdf'): all_pdfs.add(href)
            elif any(low.endswith(e) for e in ('.jpg','.jpeg','.png','.gif','.webp','.svg')):
                all_images.add(href)

    page_images = []
    for I in ex.images:
        s = I['src']
        if not s or s.startswith('data:'): continue
        if 'archive.org/static' in s or 'archive.org/images' in s: continue
        page_images.append(I)
        if 'aaro.mil' in s: all_images.add(s)

    # Extract DNN af2AccordionMenu items (Q&A pairs) — used on FAQ + similar pages
    accordion = []
    for item_html in re.findall(r'<li[^>]*class="[^"]*af2AccordionMenuListItem[^"]*"[^>]*>(.*?)</li>', src, re.S):
        # Title = first <span>… or first <a>… text
        m_title = re.search(r'<(?:span|a)[^>]*>([^<]{4,300})</(?:span|a)>', item_html)
        title_txt = m_title.group(1).strip() if m_title else ''
        # Body = full plain text minus title
        body_text = re.sub(r'<[^>]+>', ' ', item_html)
        body_text = re.sub(r'\s+', ' ', body_text).strip()
        # Strip title prefix if present
        if title_txt and body_text.startswith(title_txt):
            body_text = body_text[len(title_txt):].strip()
        if title_txt and body_text:
            accordion.append({'q': title_txt, 'a': body_text})

    results[slug] = {
        'title': title,
        'text': clean_text[:30000],
        'headings': ex.headings,
        'links': page_links[:300],
        'images': page_images[:80],
        'accordion': accordion,
    }

with open(os.path.join(CACHE_DIR, 'parsed.json'),'w') as f:
    json.dump({'pages': results, 'all_pdfs': sorted(all_pdfs), 'all_images': sorted(all_images)}, f, indent=2, ensure_ascii=False)

print(f'pages: {len(results)}, pdfs: {len(all_pdfs)}, imgs: {len(all_images)}')
