"""I18N dictionary — 6 languages, used by make_nav data-i18n attributes
and SHARED_JS' applyLang() runtime."""
from __future__ import annotations
import json as _json

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

_I18N_JSON = _json.dumps(I18N, ensure_ascii=False)
