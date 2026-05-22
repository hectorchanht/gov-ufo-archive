"""scripts/templates — split-out components of _site_template.py.

Each sub-module here owns one piece of the shared template surface:

    i18n.py       I18N dict + _I18N_JSON (UTF-8 JSON for inline scripts)
    lightbox.py   LIGHTBOX_HTML + LIGHTBOX_CSS + LIGHTBOX_JS

The top-level scripts/_site_template.py still re-exports everything for
backwards compatibility, so existing build scripts keep working without
import-path churn. Future phases will continue extracting (nav, footer,
head, shared CSS, shared JS) into this package.
"""
