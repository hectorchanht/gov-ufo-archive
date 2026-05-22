"""Backwards-compat shim for catalog-style mirror builders.

Originally housed the inline catalog-page client JS (`_CATALOG_JS`).
That body now lives in scripts/templates/archive.py as ARCHIVE_JS, with
everything else re-exported from _site_template.

UK, Brazil, Chile, batch3, and any future catalog-mirror builder can
keep using `from _mirror_shared import SHARED_CSS, SHARED_JS` unchanged.

Usage (existing scripts):
    from _mirror_shared import SHARED_CSS, SHARED_JS
    PAGE = TEMPLATE.replace('__SHARED_CSS__', SHARED_CSS).replace('__SHARED_JS__', SHARED_JS)
"""

from _site_template import (  # noqa: F401
    SHARED_CSS, make_nav, LIGHTBOX_HTML, make_footer_sources, I18N,
)
import _site_template as _T
from templates.archive import ARCHIVE_JS

# Catalog mirrors get the full nav/lightbox JS bundle plus the card-render
# + filter UI driver. ARCHIVE_JS bails out early on pages whose host
# template provides its own paginator (#pagination element present).
SHARED_JS = _T.SHARED_JS + '\n' + ARCHIVE_JS
