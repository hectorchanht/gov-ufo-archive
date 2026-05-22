#!/usr/bin/env python3
"""Merge body-level <style> blocks into <head>.

html-validate's element-permitted-content rule rejects <style> in <body>
even though modern browsers accept it. Move every body-level <style>
block back inside <head>, just before </style></head>, so the page
validates while preserving exact CSS rules order.
"""
from __future__ import annotations
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent if __file__.endswith('.py') else Path('.')

STYLE_RE = re.compile(r'<style>(.*?)</style>', re.DOTALL)

def fix(html: str) -> tuple[str, int]:
    # Split at <body>; everything after is body.
    m = re.search(r'<body[^>]*>', html)
    if not m:
        return html, 0
    head_part = html[: m.start()]
    body_part = html[m.start():]

    # Collect body <style> blocks.
    body_styles = list(STYLE_RE.finditer(body_part))
    if not body_styles:
        return html, 0

    # Concatenate body styles content.
    extra_css = '\n'.join(s.group(1).strip() for s in body_styles)

    # Strip body styles (in reverse).
    new_body = body_part
    for s in reversed(body_styles):
        # Eat surrounding blank lines to avoid leaving gaps.
        a, b = s.start(), s.end()
        # Walk back over one preceding newline if present.
        while a > 0 and new_body[a-1] == '\n':
            a -= 1
            break
        # Walk forward over one trailing newline if present.
        while b < len(new_body) and new_body[b] == '\n':
            b += 1
            break
        new_body = new_body[:a] + new_body[b:]

    # Inject extra_css before the last </style></head> in head_part.
    # Find the LAST </style> before </head>.
    end_head = head_part.rfind('</head>')
    if end_head < 0:
        return html, 0
    end_style = head_part.rfind('</style>', 0, end_head)
    if end_style < 0:
        # No existing <style> in head — insert a new one.
        new_head = head_part[:end_head] + f'<style>\n{extra_css}\n</style>\n' + head_part[end_head:]
    else:
        new_head = head_part[:end_style] + '\n' + extra_css + '\n' + head_part[end_style:]

    return new_head + new_body, len(body_styles)

def main():
    targets = sorted(p for p in ROOT.rglob('*.html')
                     if 'node_modules' not in p.parts
                     and 'aaro/pages' not in str(p))
    total_files = 0
    total_blocks = 0
    for p in targets:
        try:
            src = p.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        out, n = fix(src)
        if n:
            p.write_text(out, encoding='utf-8')
            total_files += 1
            total_blocks += n
            print(f"  {p}: merged {n} block(s)")
    print(f"\nmerged {total_blocks} <style> block(s) across {total_files} file(s)")

if __name__ == '__main__':
    main()
