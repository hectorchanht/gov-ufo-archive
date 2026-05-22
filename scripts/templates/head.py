"""Canonical <head> builder.

Returns everything from <head> through the opening of inline <style>;
caller is responsible for closing </style> and continuing the page.

Depends on SHARED_CSS + EXTRA_CSS which are still defined in
scripts/_site_template.py (will move to templates/shared.py in a future
phase). Imports them lazily to avoid circular dependencies during the
in-progress refactor.
"""
from __future__ import annotations


def make_head(title, description, canonical, og_image,
              accent_color, seal_from, seal_mid, seal_to,
              bg_tint_a='', bg_tint_b=''):
    """Return everything inside <head>...<style> (caller closes with </style>)."""
    # Lazy import: SHARED_CSS / EXTRA_CSS live in _site_template.py for now.
    # When templates/shared.py exists, switch to: from .shared import …
    import _site_template as _st
    SHARED_CSS = _st.SHARED_CSS
    EXTRA_CSS  = _st.EXTRA_CSS

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
