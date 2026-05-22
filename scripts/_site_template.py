"""Shared template for all realufo.org mirror sites.

Provides:
  - SHARED_CSS / SHARED_JS (drop-in for _mirror_shared compat)
  - make_nav(current_slug, depth, internal_links) → nav HTML
  - make_head(config) → <head> block
  - EXTRA_CSS — nav dropdown + lang picker + scroll-hide
  - EXTRA_JS  — i18n runtime + nav/lang dropdowns + scroll-hide

Design rules: CLAUDE.md § 2, 3, 6, 7.
"""

# ── Navigation config ────────────────────────────────────────────────────────

PINNED = [
    ('Home',    None,    'home'),     # href resolved by make_nav() — root search landing
    ('War.gov', 'wargov', 'wargov'),
    ('AARO',    'aaro',   'aaro'),
    ('NASA',    'nasa',   'nasa'),
    ('NARA',    'nara',   'nara'),
]
MORE = [
    ('GEIPAN (France)',    'geipan'),
    ('UK Archives',        'uk'),
    ('Brazil FAB',         'brazil'),
    ('Chile CEFAA',        'chile'),
    ('NZ NZDF',            'nz'),
    ('Canada LAC',         'canada'),
    ('Argentina CEFAe',    'argentina'),
    ('Uruguay CRIDOVNI',   'uruguay'),
    ('Peru OIFAA',         'peru'),
    ('Spain Ejército',     'spain'),
    ('Italy Aeronautica',  'italy'),
]


def _href(slug, depth):
    """Relative href from a page at `depth` to the site root of `slug`."""
    up = '../' * depth
    if slug is None:
        return up or './'         # root → index.html
    return f'{up}{slug}/'


def make_nav(current_slug: str, depth: int = 1, internal_links=None) -> str:
    """Return <nav> HTML for the sticky header.

    current_slug  — 'aaro', 'nasa', 'wargov', 'geipan', etc.
    depth         — 0 = root, 1 = mirror top, 2 = sub-page
    internal_links — list of (label, href, data_i18n_key)
    """
    # Internal (page-section) links
    int_html = ''
    if internal_links:
        for label, href, i18n_key in internal_links:
            int_html += (
                f'<li><a href="{href}" data-i18n="{i18n_key}">{label}</a></li>'
            )

    # Pinned cross-site links
    pinned_html = ''
    for name, slug, key in PINNED:
        href = _href(slug, depth)
        active = ' class="active"' if key == current_slug else ''
        pinned_html += f'<li><a href="{href}"{active}>{name}</a></li>'

    # More dropdown items
    more_items = ''.join(
        f'<li><a href="{_href(slug, depth)}">{name}</a></li>'
        for name, slug in MORE
    )

    return f'''\
    <nav class="primary" id="primary-nav">
      <ul>
        {int_html}
        <li class="nav-sep"></li>
        {pinned_html}
        <li class="has-dropdown" id="nav-more-wrap">
          <button class="nav-more-btn" id="nav-more-btn" aria-expanded="false" data-i18n="more">More ▾</button>
          <ul class="nav-dropdown" id="nav-dropdown" role="menu">
            {more_items}
          </ul>
        </li>
        <li class="lang-picker" id="lang-picker">
          <button class="lang-btn" id="lang-btn" aria-expanded="false">EN</button>
          <ul class="lang-menu" id="lang-menu" role="menu">
            <li><button data-lang="en">English</button></li>
            <li><button data-lang="fr">Français</button></li>
            <li><button data-lang="es">Español</button></li>
            <li><button data-lang="pt">Português</button></li>
            <li><button data-lang="zh">中文</button></li>
            <li><button data-lang="ja">日本語</button></li>
          </ul>
        </li>
      </ul>
    </nav>'''


def make_head(title, description, canonical, og_image,
              accent_color, seal_from, seal_mid, seal_to,
              bg_tint_a='', bg_tint_b=''):
    """Return everything inside <head>...<style> (caller closes with </style>)."""
    return f'''\
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{og_image}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="realufo.org">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{og_image}">
<link rel="icon" type="image/svg+xml" href="./assets/favicon.svg">
<link rel="apple-touch-icon" href="./assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap" rel="stylesheet">
<style>
{SHARED_CSS}
:root {{
  --caution: {accent_color};
  --seal-from: {seal_from}; --seal-mid: {seal_mid}; --seal-to: {seal_to};
}}
.seal {{ background: radial-gradient(circle at 50% 50%, var(--seal-from), var(--seal-mid) 60%, var(--seal-to)); }}
{f"body {{ background-image: radial-gradient(ellipse at 20% 0%, {bg_tint_a} 0%, transparent 50%), radial-gradient(ellipse at 80% 100%, {bg_tint_b} 0%, transparent 50%); background-attachment: fixed; }}" if bg_tint_a else ""}
{EXTRA_CSS}'''


# ── i18n dictionary ──────────────────────────────────────────────────────────

I18N = {
    'en': {'lang': 'English', 'code': 'EN', 'intro': 'Intro', 'headlines': 'Headlines',
           'archive': 'Archive', 'faq': 'About / FAQ', 'more': 'More ▾',
           'all': 'All', 'docs': 'Documents', 'videos': 'Videos', 'catalog': 'Catalog',
           'imagery': 'Imagery', 'search': 'Search…', 'total': 'Total', 'local': 'Local',
           'open_pdf': 'Open PDF', 'download': 'Download', 'source': 'Source ↗',
           'play': 'Play', 'view': 'View', 'no_results': 'No results.'},
    'fr': {'lang': 'Français', 'code': 'FR', 'intro': 'Intro', 'headlines': 'Titres',
           'archive': 'Archives', 'faq': 'À propos', 'more': 'Plus ▾',
           'all': 'Tout', 'docs': 'Documents', 'videos': 'Vidéos', 'catalog': 'Catalogue',
           'imagery': 'Images', 'search': 'Rechercher…', 'total': 'Total', 'local': 'Local',
           'open_pdf': 'Ouvrir PDF', 'download': 'Télécharger', 'source': 'Source ↗',
           'play': 'Lire', 'view': 'Voir', 'no_results': 'Aucun résultat.'},
    'es': {'lang': 'Español', 'code': 'ES', 'intro': 'Intro', 'headlines': 'Titulares',
           'archive': 'Archivo', 'faq': 'Acerca de', 'more': 'Más ▾',
           'all': 'Todo', 'docs': 'Documentos', 'videos': 'Videos', 'catalog': 'Catálogo',
           'imagery': 'Imágenes', 'search': 'Buscar…', 'total': 'Total', 'local': 'Local',
           'open_pdf': 'Abrir PDF', 'download': 'Descargar', 'source': 'Fuente ↗',
           'play': 'Reproducir', 'view': 'Ver', 'no_results': 'Sin resultados.'},
    'pt': {'lang': 'Português', 'code': 'PT', 'intro': 'Intro', 'headlines': 'Destaques',
           'archive': 'Arquivo', 'faq': 'Sobre', 'more': 'Mais ▾',
           'all': 'Tudo', 'docs': 'Documentos', 'videos': 'Vídeos', 'catalog': 'Catálogo',
           'imagery': 'Imagens', 'search': 'Pesquisar…', 'total': 'Total', 'local': 'Local',
           'open_pdf': 'Abrir PDF', 'download': 'Baixar', 'source': 'Fonte ↗',
           'play': 'Reproduzir', 'view': 'Ver', 'no_results': 'Sem resultados.'},
    'zh': {'lang': '中文', 'code': '中文', 'intro': '介绍', 'headlines': '要闻',
           'archive': '档案', 'faq': '关于', 'more': '更多 ▾',
           'all': '全部', 'docs': '文件', 'videos': '视频', 'catalog': '目录',
           'imagery': '图像', 'search': '搜索…', 'total': '总计', 'local': '本地',
           'open_pdf': '打开 PDF', 'download': '下载', 'source': '来源 ↗',
           'play': '播放', 'view': '查看', 'no_results': '无结果。'},
    'ja': {'lang': '日本語', 'code': 'JP', 'intro': 'はじめに', 'headlines': 'ヘッドライン',
           'archive': 'アーカイブ', 'faq': 'について', 'more': 'もっと ▾',
           'all': 'すべて', 'docs': '書類', 'videos': 'ビデオ', 'catalog': 'カタログ',
           'imagery': '画像', 'search': '検索…', 'total': '合計', 'local': 'ローカル',
           'open_pdf': 'PDF を開く', 'download': 'ダウンロード', 'source': 'ソース ↗',
           'play': '再生', 'view': '表示', 'no_results': '結果なし。'},
}

import json as _json
_I18N_JSON = _json.dumps(I18N, ensure_ascii=False)

# ── CSS ──────────────────────────────────────────────────────────────────────

SHARED_CSS = r'''
:root {
  --bg:#0a0a0c; --bg-2:#111114; --panel:#15151a;
  --ink:#e8e3d8; --ink-dim:#a8a298; --ink-faint:#6b665d;
  --rule:rgba(232,227,216,0.12); --rule-strong:rgba(232,227,216,0.28);
  --stamp:#b91c1c; --warm:#d4a017; --classified:#c9362c;
  --serif:"Source Serif 4","Iowan Old Style",Georgia,serif;
  --mono:"JetBrains Mono","SF Mono",Consolas,monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; scroll-padding-top: 70px; }
body { background: var(--bg); color: var(--ink); font-family: var(--serif); font-size: 15px; line-height: 1.65; overflow-x: hidden; }
@media (min-width: 720px) { body { font-size: 16px; } }
.scanlines { position: fixed; inset: 0; background: repeating-linear-gradient(to bottom, transparent 0, transparent 2px, rgba(255,255,255,0.012) 3px, transparent 4px); pointer-events: none; z-index: 50; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 16px; position: relative; z-index: 2; }
@media (min-width: 720px) { .container { padding: 0 32px; } }

/* ── Header ─────────────────────────────────────────────────────────── */
.header-wrap { position: sticky; top: 0; z-index: 40; background: rgba(10,10,12,0.96); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid var(--rule); }
header { padding: 12px 0; }
header .container { display: flex; align-items: center; gap: 12px; }
.brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: var(--ink); flex-shrink: 0; min-width: 0; }
.seal { width: 38px; height: 38px; border-radius: 50%; display: grid; place-items: center; box-shadow: 0 0 0 2px var(--ink), 0 0 0 4px var(--bg), 0 0 0 5px var(--ink-faint); font-family: var(--mono); font-weight: 700; font-size: 9px; color: var(--ink); flex-shrink: 0; }
.brand-text { display: flex; flex-direction: column; line-height: 1.1; min-width: 0; }
.brand-text .super { font-family: var(--mono); font-size: 8.5px; letter-spacing: 0.14em; color: var(--ink-dim); text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 180px; }
.brand-text .name { font-family: var(--serif); font-size: 15px; font-weight: 600; margin-top: 1px; }
@media (min-width: 720px) { .seal { width: 42px; height: 42px; } .brand-text .name { font-size: 17px; } .brand-text .super { max-width: none; } }

/* Hamburger — right-most, never pushed to next line */
.nav-toggle { display: none; background: transparent; border: 1px solid var(--rule-strong); width: 38px; height: 38px; cursor: pointer; padding: 0; flex-direction: column; justify-content: center; align-items: center; gap: 4px; flex-shrink: 0; margin-left: auto; }
.nav-toggle span { display: block; width: 18px; height: 2px; background: var(--ink); transition: transform .2s, opacity .2s; }
.nav-toggle[aria-expanded="true"] span:nth-child(1) { transform: translateY(6px) rotate(45deg); }
.nav-toggle[aria-expanded="true"] span:nth-child(2) { opacity: 0; }
.nav-toggle[aria-expanded="true"] span:nth-child(3) { transform: translateY(-6px) rotate(-45deg); }

/* ── Primary nav ─────────────────────────────────────────────────────── */
nav.primary { display: none; flex-basis: 100%; font-family: var(--mono); font-size: 11px; letter-spacing: 0.07em; }
nav.primary.open { display: block; }
nav.primary > ul { display: flex; flex-direction: column; gap: 0; list-style: none; padding-top: 10px; margin-top: 10px; border-top: 1px solid var(--rule); }
nav.primary > ul > li { width: 100%; }
nav.primary > ul > li.nav-sep { display: none; }
nav.primary a { color: var(--ink-dim); text-decoration: none; text-transform: uppercase; display: block; padding: 11px 0; border-bottom: 1px solid var(--rule); }
nav.primary a:hover, nav.primary a.active { color: var(--caution); }

@media (min-width: 720px) {
  .nav-toggle { display: none !important; }
  nav.primary { display: flex !important; flex-basis: auto; flex: 1; align-items: center; justify-content: flex-end; }
  nav.primary > ul { flex-direction: row; align-items: center; gap: 2px 18px; flex-wrap: nowrap; padding-top: 0; margin-top: 0; border: 0; }
  nav.primary > ul > li { width: auto; }
  nav.primary a { padding: 0; border: 0; font-size: 10.5px; }
  nav.primary > ul > li.nav-sep { display: block; width: 1px; height: 16px; background: var(--rule-strong); flex-shrink: 0; }
}

/* mobile hamburger visible only below 720px */
@media (max-width: 719px) {
  .nav-toggle { display: flex; }
}

/* ── "More" dropdown ─────────────────────────────────────────────────── */
.has-dropdown { position: relative; }
.nav-more-btn {
  background: none; border: none; color: var(--ink-dim); cursor: pointer;
  font-family: var(--mono); font-size: 11px; letter-spacing: 0.07em;
  text-transform: uppercase; padding: 11px 0; display: block; width: 100%;
  text-align: left; border-bottom: 1px solid var(--rule);
}
.nav-more-btn:hover { color: var(--caution); }
.nav-dropdown {
  display: none; list-style: none;
  background: var(--panel); border: 1px solid var(--rule-strong);
  padding: 6px 0; z-index: 200;
}
.nav-dropdown li a { border: 0 !important; padding: 9px 16px !important; font-size: 10.5px; white-space: nowrap; }
/* Mobile: inline expansion */
@media (max-width: 719px) {
  .has-dropdown.open .nav-dropdown { display: block; margin: 0 0 0 12px; border: 0; background: transparent; }
}
/* Desktop: floating dropdown */
@media (min-width: 720px) {
  .nav-more-btn { padding: 0; border: 0; width: auto; font-size: 10.5px; }
  .nav-dropdown { position: absolute; right: 0; top: calc(100% + 10px); min-width: 180px; }
  .has-dropdown:hover .nav-dropdown,
  .has-dropdown:focus-within .nav-dropdown { display: block; }
}

/* ── Language picker ─────────────────────────────────────────────────── */
.lang-picker { position: relative; }
.lang-btn {
  background: transparent; border: 1px solid var(--rule-strong);
  color: var(--ink-dim); cursor: pointer; font-family: var(--mono);
  font-size: 9.5px; letter-spacing: 0.12em; padding: 4px 8px;
  text-transform: uppercase; transition: color .15s, border-color .15s;
  display: block; width: 100%; text-align: left; margin: 8px 0;
}
.lang-btn:hover { color: var(--caution); border-color: var(--caution); }
.lang-menu { display: none; list-style: none; background: var(--panel); border: 1px solid var(--rule-strong); padding: 6px 0; z-index: 300; }
.lang-menu button { background: none; border: none; color: var(--ink-dim); cursor: pointer; font-family: var(--mono); font-size: 10.5px; padding: 8px 16px; width: 100%; text-align: left; }
.lang-menu button:hover { color: var(--caution); }
.lang-picker.open .lang-menu { display: block; }
@media (max-width: 719px) {
  .lang-btn { border: 0; margin: 0; padding: 11px 0; font-size: 11px; border-bottom: 1px solid var(--rule); }
  .lang-picker.open .lang-menu { margin-left: 12px; border: 0; background: transparent; }
}
@media (min-width: 720px) {
  .lang-btn { width: auto; margin: 0; padding: 3px 8px; }
  .lang-menu { position: absolute; right: 0; top: calc(100% + 10px); min-width: 130px; }
}

/* ── Hero ────────────────────────────────────────────────────────────── */
.hero { padding: 48px 0 32px; border-bottom: 1px solid var(--rule); }
@media (min-width: 720px) { .hero { padding: 64px 0 48px; } }
.coords { font-family: var(--mono); font-size: 11px; color: var(--caution); letter-spacing: 0.12em; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.coords::before { content: "◉"; color: var(--stamp); }
h1.hero-title { font-family: var(--serif); font-weight: 700; font-size: clamp(26px,5.5vw,52px); line-height: 1.05; letter-spacing: -0.02em; max-width: 24ch; margin-bottom: 18px; word-break: break-word; }
h1.hero-title em { color: var(--caution); font-style: italic; }
.hero-sub { max-width: 65ch; color: var(--ink-dim); font-size: 16px; line-height: 1.65; }
.hero-sub a { color: var(--caution); }

/* ── Headlines ───────────────────────────────────────────────────────── */
.headlines { padding: 32px 0; border-bottom: 1px solid var(--rule); }
.head-grid { display: grid; gap: 14px; grid-template-columns: 1fr; }
@media (min-width: 540px) { .head-grid { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; } }
.head-card { padding: 18px 20px; background: var(--panel); border: 1px solid var(--rule); border-left: 3px solid var(--caution); }
.head-card .h-label { font-family: var(--mono); font-size: 10px; color: var(--caution); letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 10px; }
.head-card .h-text { font-size: 16px; line-height: 1.4; color: var(--ink); }
.head-card .h-num { font-family: var(--mono); font-size: 28px; color: var(--ink); font-weight: 600; display: block; margin-bottom: 4px; }

/* ── Archive section ─────────────────────────────────────────────────── */
section { padding: 40px 0; border-bottom: 1px solid var(--rule); }
@media (min-width: 720px) { section { padding: 56px 0; } }
.section-label { font-family: var(--mono); font-size: 11px; letter-spacing: 0.24em; text-transform: uppercase; color: var(--ink-faint); display: flex; align-items: center; gap: 14px; margin-bottom: 18px; }
.section-label::before { content: ""; width: 28px; height: 1px; background: var(--ink-faint); }
h2 { font-family: var(--serif); font-size: clamp(22px,3.5vw,34px); font-weight: 700; letter-spacing: -0.015em; margin-bottom: 18px; max-width: 28ch; word-break: break-word; }
.lede { max-width: 70ch; color: var(--ink); font-size: 16px; }
.lede a { color: var(--caution); }

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1px; background: var(--rule); border: 1px solid var(--rule); margin: 20px 0 24px; }
@media (min-width: 540px) { .stats-grid { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); } }
.stat { background: var(--panel); padding: 14px 18px; font-family: var(--mono); }
.stat b { display: block; font-size: 24px; color: var(--ink); font-weight: 500; }
.stat small { display: block; font-size: 10px; color: var(--ink-faint); letter-spacing: 0.16em; text-transform: uppercase; margin-top: 6px; }

/* ── Archive controls (tabs + search) — stays sticky ─────────────────── */
.arch-controls-bar {
  position: sticky; top: 64px; z-index: 30;
  background: rgba(10,10,12,0.96); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule);
  margin: 24px -16px 0; padding: 10px 16px;
  display: flex; flex-direction: column; gap: 8px;
  transition: top 0.28s ease;
}
@media (min-width: 720px) {
  .arch-controls-bar { margin: 24px -32px 0; padding: 12px 32px; flex-direction: row; align-items: center; gap: 14px; }
}
.arch-controls-bar.bar-hidden { top: -160px; }

.tabs { display: flex; gap: 6px; flex-wrap: wrap; width: 100%; }
.tab { font-family: var(--mono); font-size: 10px; padding: 6px 10px; border: 1px solid var(--rule-strong); background: var(--panel); color: var(--ink-dim); cursor: pointer; letter-spacing: 0.08em; text-transform: uppercase; }
@media (min-width: 720px) { .tab { font-size: 11px; padding: 8px 14px; } .tabs { width: auto; } }
.tab:hover { color: var(--ink); border-color: var(--ink-faint); }
.tab.active { background: var(--caution); color: var(--bg); border-color: var(--caution); font-weight: 700; }
.tab .count { opacity: 0.6; margin-left: 6px; font-size: 10px; }

.search-wrap { display: flex; align-items: center; gap: 8px; background: var(--panel); border: 1px solid var(--rule-strong); padding: 6px 12px; width: 100%; }
@media (min-width: 720px) { .search-wrap { margin-left: auto; min-width: 240px; width: auto; } }
.search-wrap::before { content: "⌕"; color: var(--ink-faint); font-family: var(--mono); }
.search-wrap input { background: transparent; border: 0; outline: 0; color: var(--ink); font-family: var(--mono); font-size: 12px; flex: 1; min-width: 0; }
.search-wrap input::placeholder { color: var(--ink-faint); }

/* ── Cards ───────────────────────────────────────────────────────────── */
.arch-grid { display: grid; grid-template-columns: 1fr; gap: 14px; padding: 16px 0 24px; }
@media (min-width: 540px) { .arch-grid { grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 18px; } }
.card { background: var(--panel); border: 1px solid var(--rule); display: flex; flex-direction: column; overflow: hidden; transition: border-color .2s, transform .2s; }
.card:hover { border-color: var(--caution); transform: translateY(-2px); }
.card-media { aspect-ratio: 16/9; background: var(--bg-2); position: relative; overflow: hidden; display: grid; place-items: center; border-bottom: 1px solid var(--rule); cursor: pointer; }
.card-media img { width: 100%; height: 100%; object-fit: cover; display: block; }
.pdf-glyph { font-family: var(--mono); font-size: 12px; color: var(--ink-faint); background: repeating-linear-gradient(45deg,#1a1a1f,#1a1a1f 8px,#15151a 8px,#15151a 16px); width: 100%; height: 100%; display: grid; place-items: center; text-align: center; padding: 16px; }
.pdf-glyph .ico { font-size: 22px; color: var(--caution); margin-bottom: 6px; border: 2px solid var(--caution); padding: 4px 10px; font-weight: 700; letter-spacing: 0.04em; display: inline-block; }
.glyph-cat { background: linear-gradient(135deg, rgba(212,160,23,0.12), transparent); }
.glyph-cat .ico { color: var(--warm); border-color: var(--warm); }
.badge { position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.78); color: var(--caution); font-family: var(--mono); font-size: 9px; padding: 3px 8px; letter-spacing: 0.14em; text-transform: uppercase; }
.badge.local { bottom: 8px; left: 8px; top: auto; color: var(--warm); }
.badge.source { bottom: 8px; left: 8px; top: auto; color: var(--ink-faint); }
.card-body { padding: 14px 16px; flex: 1; display: flex; flex-direction: column; gap: 6px; }
.card-title { font-family: var(--serif); font-size: 14px; font-weight: 600; line-height: 1.35; color: var(--ink); overflow-wrap: anywhere; }
.card-desc { font-family: var(--serif); font-size: 12.5px; color: var(--ink-dim); line-height: 1.5; margin-top: 4px; }
.card-meta { display: grid; grid-template-columns: 72px 1fr; gap: 4px 12px; margin-top: 8px; padding: 10px 0; border-top: 1px solid var(--rule); }
.card-meta dt { font-family: var(--mono); font-size: 9px; color: var(--ink-faint); letter-spacing: 0.14em; text-transform: uppercase; }
.card-meta dd { font-family: var(--serif); color: var(--ink); font-size: 12px; line-height: 1.4; }
.card-actions { display: flex; gap: 8px; margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--rule); flex-wrap: wrap; }
.card-actions a, .card-actions button { font-family: var(--mono); font-size: 10px; color: var(--caution); text-decoration: none; letter-spacing: 0.12em; text-transform: uppercase; padding: 6px 10px; border: 1px solid var(--rule-strong); min-height: 30px; display: inline-flex; align-items: center; background: none; cursor: pointer; }
.card-actions a:hover, .card-actions button:hover { background: var(--caution); color: var(--bg); border-color: var(--caution); }
.card-actions .warn { color: var(--ink-faint); }
.card-actions .warn:hover { background: var(--ink-faint); color: var(--bg); }
.empty { padding: 60px 0; text-align: center; color: var(--ink-faint); font-family: var(--mono); font-size: 13px; }

/* ── Lightbox ─────────────────────────────────────────────────────────── */
.lightbox { position: fixed; inset: 0; background: rgba(0,0,0,0.94); display: none; place-items: center; z-index: 200; padding: 16px; }
@media (min-width: 720px) { .lightbox { padding: 32px; } }
.lightbox.open { display: grid; }
.lb-inner { max-width: 92vw; max-height: 92vh; display: flex; flex-direction: column; gap: 10px; align-items: center; }
.lb-inner img, .lb-inner video { max-width: 90vw; max-height: 78vh; border: 1px solid var(--rule-strong); background: #000; }
.lb-inner iframe { width: 92vw; height: 84vh; border: 1px solid var(--rule-strong); background: #fff; }
.lb-meta { font-family: var(--mono); font-size: 11px; color: var(--ink); background: var(--bg-2); border: 1px solid var(--rule-strong); padding: 8px 14px; max-width: 90vw; text-align: center; }
.lb-meta a { color: var(--caution); }
.lb-close { position: absolute; top: 12px; right: 12px; width: 40px; height: 40px; background: var(--bg-2); border: 1px solid var(--rule-strong); color: var(--ink); display: grid; place-items: center; cursor: pointer; font-family: var(--mono); font-size: 22px; z-index: 2; }
.lb-nav { position: absolute; top: 50%; transform: translateY(-50%); width: 40px; height: 40px; background: rgba(20,20,24,0.6); border: 1px solid var(--rule-strong); color: var(--ink); display: grid; place-items: center; cursor: pointer; font-family: var(--serif); font-size: 24px; z-index: 2; transition: background .15s, color .15s, border-color .15s; }
@media (min-width: 720px) { .lb-nav { width: 52px; height: 52px; font-size: 32px; } }
.lb-nav:hover { background: rgba(0,0,0,0.85); color: var(--caution); border-color: var(--caution); }
.lb-nav.prev { left: 8px; } .lb-nav.next { right: 8px; }
@media (min-width: 720px) { .lb-nav.prev { left: 16px; } .lb-nav.next { right: 16px; } }
.lb-counter { position: absolute; top: 16px; left: 50%; transform: translateX(-50%); font-family: var(--mono); font-size: 11px; letter-spacing: 0.16em; color: var(--ink-dim); background: var(--bg-2); border: 1px solid var(--rule); padding: 4px 12px; z-index: 2; }

/* ── Footer ──────────────────────────────────────────────────────────── */
footer { background: #060608; padding: 32px 0 24px; color: var(--ink-dim); font-family: var(--mono); font-size: 12px; }
footer .container { display: grid; grid-template-columns: 1fr; gap: 24px; }
@media (min-width: 720px) { footer .container { grid-template-columns: 1.4fr 1fr 1fr; gap: 40px; } }
footer h4 { font-family: var(--mono); font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--ink); margin-bottom: 14px; }
footer ul { list-style: none; display: flex; flex-direction: column; gap: 8px; }
footer a { color: var(--ink-dim); text-decoration: none; }
footer a:hover { color: var(--caution); }
footer .colophon { grid-column: 1 / -1; border-top: 1px solid var(--rule); padding-top: 20px; margin-top: 12px; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 16px; font-size: 10px; color: var(--ink-faint); letter-spacing: 0.1em; }
'''

# Extra CSS that extends SHARED_CSS (included automatically by make_head)
EXTRA_CSS = ''  # already included in SHARED_CSS above

# ── JS ───────────────────────────────────────────────────────────────────────

SHARED_JS = r'''
(() => {
  /* ── i18n ─────────────────────────────────────────────────────────── */
  const I18N = __I18N_JSON__;
  let lang = localStorage.getItem('realufo_lang') || 'en';
  if (!I18N[lang]) lang = 'en';

  function applyLang(code) {
    lang = code;
    localStorage.setItem('realufo_lang', code);
    const t = I18N[code];
    // Update all data-i18n elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (t[key] !== undefined) el.textContent = t[key];
    });
    // Update lang button label
    const lb = document.getElementById('lang-btn');
    if (lb) lb.textContent = t.code || code.toUpperCase();
    // Update tab labels if archive page
    updateTabLabels(t);
  }

  function updateTabLabels(t) {
    const TAB_MAP = { ALL: t.all, PDF: t.docs, VID: t.videos,
                      IMG: t.imagery, CATALOG: t.catalog };
    document.querySelectorAll('.tab[data-key]').forEach(btn => {
      const key = btn.dataset.key;
      if (TAB_MAP[key]) {
        const count = btn.querySelector('.count');
        const countText = count ? count.outerHTML : '';
        btn.innerHTML = TAB_MAP[key] + countText;
        if (count) btn.appendChild(btn.querySelector('.count'));
      }
    });
    const si = document.getElementById('arch-search');
    if (si) si.setAttribute('placeholder', t.search || 'Search…');
    const empty = document.getElementById('arch-empty');
    if (empty) empty.textContent = t.no_results || 'No results.';
  }

  /* ── Language picker ──────────────────────────────────────────────── */
  const langPicker = document.getElementById('lang-picker');
  const langBtn    = document.getElementById('lang-btn');
  const langMenu   = document.getElementById('lang-menu');
  if (langBtn && langPicker) {
    langBtn.addEventListener('click', e => {
      e.stopPropagation();
      const open = langPicker.classList.toggle('open');
      langBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    if (langMenu) {
      langMenu.addEventListener('click', e => {
        const btn = e.target.closest('button[data-lang]');
        if (!btn) return;
        applyLang(btn.dataset.lang);
        langPicker.classList.remove('open');
        langBtn.setAttribute('aria-expanded', 'false');
      });
    }
  }

  /* ── "More" dropdown ──────────────────────────────────────────────── */
  const moreWrap = document.getElementById('nav-more-wrap');
  const moreBtn  = document.getElementById('nav-more-btn');
  if (moreWrap && moreBtn) {
    moreBtn.addEventListener('click', e => {
      e.stopPropagation();
      const open = moreWrap.classList.toggle('open');
      moreBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  /* Close dropdowns on outside click */
  document.addEventListener('click', () => {
    if (langPicker) { langPicker.classList.remove('open'); if (langBtn) langBtn.setAttribute('aria-expanded','false'); }
    if (moreWrap)  { moreWrap.classList.remove('open');  if (moreBtn) moreBtn.setAttribute('aria-expanded','false'); }
  });

  /* ── Hamburger toggle ─────────────────────────────────────────────── */
  const navToggle = document.getElementById('nav-toggle');
  const primaryNav = document.getElementById('primary-nav');
  if (navToggle && primaryNav) {
    navToggle.addEventListener('click', () => {
      const open = primaryNav.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    primaryNav.addEventListener('click', e => {
      if (e.target.tagName === 'A') {
        primaryNav.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ── Scroll-hide controls bar (mobile) ───────────────────────────── */
  const ctrlBar = document.querySelector('.arch-controls-bar');
  if (ctrlBar) {
    let lastY = window.scrollY;
    window.addEventListener('scroll', () => {
      if (window.innerWidth >= 720) { ctrlBar.classList.remove('bar-hidden'); return; }
      const y = window.scrollY;
      if (y < 80) { ctrlBar.classList.remove('bar-hidden'); }
      else if (y > lastY + 4) { ctrlBar.classList.add('bar-hidden'); }
      else if (y < lastY - 4) { ctrlBar.classList.remove('bar-hidden'); }
      lastY = y;
    }, { passive: true });
  }

  /* Apply saved language */
  applyLang(lang);

  /* ── Lightbox ─────────────────────────────────────────────────────── */
  let lbList = [], lbIdx = 0;
  const lb      = document.getElementById('lightbox');
  const lbI     = document.getElementById('lb-inner');
  const lbC     = document.getElementById('lb-close');
  const lbPrev  = document.getElementById('lb-prev');
  const lbNext  = document.getElementById('lb-next');
  const lbCount = document.getElementById('lb-counter');

  function esc(s) {
    return (s||'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function renderLb() {
    const a = lbList[lbIdx]; if (!a) return;
    const title = a.ti || a.title || '';
    let html;
    if (a.t === 'IMG' || a.type === 'IMG') {
      const src = a.l || a.local ? './' + (a.l || a.local) : (a.u || a.url);
      const fb  = (a.u || a.url) && (a.l || a.local) ? `onerror="this.onerror=null;this.src='${esc(a.u||a.url)}';"` : '';
      html = `<img src="${esc(src)}" alt="${esc(title)}" ${fb}><div class="lb-meta">${esc(title)}</div>`;
    } else if (a.t === 'VID' || a.type === 'VID') {
      const loc = a.l || a.local; const rem = a.u || a.url;
      if (loc) {
        html = `<video controls autoplay style="max-width:90vw;max-height:78vh"><source src="./${esc(loc)}"><source src="${esc(rem)}"></video><div class="lb-meta">${esc(title)}</div>`;
      } else if (a.embed) {
        html = `<iframe src="${esc(a.embed)}?autoplay=1" allow="autoplay;encrypted-media" allowfullscreen></iframe><div class="lb-meta">${esc(title)}</div>`;
      } else { window.open(rem,'_blank'); closeLb(); return; }
    } else if (a.t === 'PDF' || a.type === 'PDF') {
      const loc = a.l || a.local;
      if (loc) {
        html = `<iframe src="./${esc(loc)}#view=FitH" sandbox="allow-same-origin allow-popups"></iframe><div class="lb-meta">${esc(title)} — <a href="./${esc(loc)}" target="_blank">open in new tab ↗</a></div>`;
      } else { window.open(a.u || a.url,'_blank'); closeLb(); return; }
    } else {
      const target = (a.l||a.local) ? './'+(a.l||a.local) : (a.u||a.url);
      window.open(target,'_blank'); closeLb(); return;
    }
    lbI.innerHTML = html;
    if (lbCount) lbCount.textContent = (lbIdx+1) + ' / ' + lbList.length;
    if (lbPrev) lbPrev.style.visibility = lbList.length > 1 ? 'visible' : 'hidden';
    if (lbNext) lbNext.style.visibility = lbList.length > 1 ? 'visible' : 'hidden';
  }
  function openAt(idx) { if (!lbList.length) return; lbIdx = (idx+lbList.length)%lbList.length; renderLb(); lb && lb.classList.add('open'); }
  function navLb(d)  { if (!lbList.length) return; lbIdx = (lbIdx+d+lbList.length)%lbList.length; renderLb(); }
  function closeLb() { lb && lb.classList.remove('open'); lbI && (lbI.innerHTML=''); }

  if (lb) {
    if (lbC)    lbC.addEventListener('click', closeLb);
    if (lbPrev) lbPrev.addEventListener('click', e => { e.stopPropagation(); navLb(-1); });
    if (lbNext) lbNext.addEventListener('click', e => { e.stopPropagation(); navLb(1); });
    lb.addEventListener('click', e => { if (e.target === lb) closeLb(); });
  }
  document.addEventListener('keydown', e => {
    if (!lb || !lb.classList.contains('open')) return;
    if (e.key==='Escape') closeLb();
    else if (e.key==='ArrowRight') navLb(1);
    else if (e.key==='ArrowLeft')  navLb(-1);
  });
  let tx=0, ty=0, tt=0;
  if (lb) {
    lb.addEventListener('touchstart', e => { if (!e.touches.length) return; tx=e.touches[0].clientX; ty=e.touches[0].clientY; tt=Date.now(); }, {passive:true});
    lb.addEventListener('touchend',   e => { if (!e.changedTouches.length) return; const dx=e.changedTouches[0].clientX-tx, dy=e.changedTouches[0].clientY-ty; if(Date.now()-tt<800&&Math.abs(dx)>50&&Math.abs(dx)>Math.abs(dy)) navLb(dx<0?1:-1); }, {passive:true});
  }

  /* Export for caller scripts that need openAt/lbList */
  window._lb = { open: openAt, setList: l => { lbList = l; }, getList: () => lbList };
})();
'''.replace('__I18N_JSON__', _I18N_JSON)


# ── Lightbox HTML fragment ───────────────────────────────────────────────────

LIGHTBOX_HTML = '''\
<div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Media viewer">
  <div class="lb-inner" id="lb-inner"></div>
  <button class="lb-close" id="lb-close" aria-label="Close (Escape)">✕</button>
  <button class="lb-nav prev" id="lb-prev" aria-label="Previous (←)">‹</button>
  <button class="lb-nav next" id="lb-next" aria-label="Next (→)">›</button>
  <div class="lb-counter" id="lb-counter"></div>
</div>'''


# ── Footer nav fragment ───────────────────────────────────────────────────────

def make_footer_sources(source_links, license_text='', colophon=''):
    """Return footer HTML.

    source_links — list of (label, url) for official sources
    """
    links_html = '\n'.join(
        f'<li><a href="{url}" target="_blank" rel="noopener">{label}</a></li>'
        for label, url in source_links
    )
    sites_html = ''.join(
        f'<li><a href="{_href(slug,1)}">{name}</a></li>'
        for name, slug in [
            ('War.gov / UFO', None), ('AARO', 'aaro'), ('NASA', 'nasa'),
            ('NARA', 'nara'), ('GEIPAN', 'geipan'), ('UK Archives', 'uk'),
            ('Brazil FAB', 'brazil'), ('Chile CEFAA', 'chile'),
        ]
    )
    return f'''\
<footer>
  <div class="container">
    <div>
      <h4>Official Sources</h4>
      <ul>{links_html}</ul>
    </div>
    <div>
      <h4>All Sites</h4>
      <ul>{sites_html}</ul>
    </div>
    <div>
      <h4>Project</h4>
      <ul>
        <li><a href="https://realufo.org/">realufo.org</a></li>
        <li><a href="https://github.com/hectorchanht/war-gov-ufo-release">GitHub</a></li>
      </ul>
      {f'<p style="margin-top:14px;font-size:10px;color:var(--ink-faint);line-height:1.6;">{license_text}</p>' if license_text else ''}
    </div>
    <div class="colophon">{colophon if colophon else 'All content is sourced from official government archives and is in the public domain.'}</div>
  </div>
</footer>'''
