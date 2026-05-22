"""Shared template for all realufo.org mirror sites.

Provides:
  - SHARED_CSS / SHARED_JS (drop-in for _mirror_shared compat)
  - make_nav(current_slug, depth, internal_links) → nav HTML
  - make_head(config) → <head> block
  - EXTRA_CSS — nav dropdown + lang picker + scroll-hide
  - EXTRA_JS  — i18n runtime + nav/lang dropdowns + scroll-hide

Design rules: CLAUDE.md § 2, 3, 6, 7.
"""

# ── Navigation, footer, head ─────────────────────────────────────────────────
# All three now live under scripts/templates/. Re-exported here for backwards
# compat — every `from _site_template import make_nav` / PINNED / etc.
# keeps working unchanged.

# Set up sys.path so the templates package is importable when this module is
# loaded by Python files outside the scripts/ directory.
import os as _os, sys as _sys  # noqa: E402
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from templates.nav import (  # noqa: E402,F401
    PINNED, SITE_PAGES, MORE, STORIES, _href, make_nav,
)
from templates.footer import (  # noqa: E402,F401
    make_footer, make_footer_sources,
)
from templates.head import make_head  # noqa: E402,F401


# ── i18n dictionary ──────────────────────────────────────────────────────────
# Lives in scripts/templates/i18n.py. Re-exported here for backwards compat.
from templates.i18n import I18N, _I18N_JSON  # noqa: E402,F401


# ── CSS + JS ────────────────────────────────────────────────────────────────
# Live in scripts/templates/shared.py. SHARED_CSS already has the lightbox
# rules injected; SHARED_JS has _I18N_JSON injected. Re-exported here for
# backwards compat — every existing `from _site_template import SHARED_CSS,
# SHARED_JS, EXTRA_CSS` continues to work unchanged.
from templates.shared import SHARED_CSS, EXTRA_CSS, SHARED_JS  # noqa: E402,F401


# ── Lightbox: HTML + CSS + JS ────────────────────────────────────────────────
# Definitions live in scripts/templates/lightbox.py. Re-exported here for
# backwards compat with every existing `from _site_template import LIGHTBOX_*`.
from templates.lightbox import LIGHTBOX_HTML, LIGHTBOX_CSS, LIGHTBOX_JS  # noqa: E402,F401
