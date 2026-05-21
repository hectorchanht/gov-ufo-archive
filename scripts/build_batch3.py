#!/usr/bin/env python3
"""Generate seven national mirror sites in one pass — NZ, Canada, Argentina,
Uruguay, Peru, Spain, Italy. Same shared template + tone-colour per country.

Re-running rebuilds every mirror from the canonical CONFIG below.
"""
import json, os, sys, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _mirror_shared import SHARED_CSS, SHARED_JS

# ============================================================
# Country definitions
# ============================================================
CONFIG = [
    {
        'slug': 'nz',
        'name': 'NZDF UFO Files',
        'seal_label': 'NZDF',
        'super': 'New Zealand Defence Force · Archives NZ',
        'tone': '#5b8def',
        'seal_from': '#000000', 'seal_mid': '#333333', 'seal_to': '#000000',
        'bg_tint_a': 'rgba(207,20,43,0.05)', 'bg_tint_b': 'rgba(0,0,0,0.04)',
        'page_title': 'NZDF UFO Files — Archives New Zealand (Offline Mirror)',
        'meta_desc': "Offline mirror of New Zealand's declassified MoD/RNZAF UFO files at Archives New Zealand — 2,010 pages spanning 1952-2009.",
        'og_title': 'NZDF UFO Files — Archives New Zealand | realufo.org',
        'og_desc':  "New Zealand's declassified UFO archive (1952-2009). 2,010 pages including AIR 1080/6/897 (Kaikoura 1978). Held at Archives NZ.",
        'og_image': 'https://realufo.org/slideshow/FBI-Photo-A5.jpg',
        'coords': '41°17′S, 174°47′E · WELLINGTON · ARCHIVES NEW ZEALAND',
        'h1_pre':  "New Zealand's ",
        'h1_em':   'declassified',
        'h1_post': ' RNZAF UFO files.',
        'hero_html': """
            In <strong>December 2010</strong>, the New Zealand Defence Force released
            <strong>2,010 pages</strong> of previously classified UFO files (1952-2009) to
            Archives New Zealand. Centrepiece: the AIR 1080/6/897 series on the
            <strong>1978 Kaikoura sightings</strong>. Released after a 14-month campaign by
            UFOCUS NZ. Source: <a href=\"https://www.archives.govt.nz/\" target=\"_blank\" rel=\"noopener\">archives.govt.nz</a>.
        """,
        'headlines': [
            ('Release', '<span class="h-num">2010</span><div class="h-text">First tranche on 22 Dec; second tranche embargoed to 31 Mar 2011.</div>'),
            ('Pages', '<span class="h-num">2 010</span><div class="h-text">12 volumes (tranche 1) + 3 volumes (tranche 2).</div>'),
            ('Span', '<div class="h-text"><strong>1952 — 2009</strong> · 57 years of RNZAF correspondence.</div>'),
            ('Flagship', '<div class="h-text">Kaikoura 1978 — AIR 1080/6/897 (still unexplained).</div>'),
            ('Custodian', '<div class="h-text">Archives New Zealand · Wellington.</div>'),
            ('Trigger', '<div class="h-text">14-month OIA campaign by UFOCUS NZ.</div>'),
        ],
        'assets': [
            {
                't': 'PDF',
                'ti': 'NZDF — UAP/UFO/USO OIA response (2023-4763)',
                'de': "NZDF's response to a 2023 OIA request on contemporary UAP/UFO/USO reporting procedure. Confirms NZDF no longer maintains a UFO file but redirects to Civil Aviation Authority.",
                'ag': 'NZDF',
                'cat': 'OIA',
                'date': 'Jul 2023',
                'u': 'https://www.nzdf.mil.nz/assets/Uploads/DocumentLibrary/OIA-2023-4763_UAP-UFO-USO.pdf',
                's': 'https://www.nzdf.mil.nz/assets/Uploads/DocumentLibrary/OIA-2023-4763_UAP-UFO-USO.pdf',
            },
            {
                't': 'PDF',
                'ti': 'NZDF — UFO/UAP reporting OIA response (2024-5199)',
                'de': "More recent OIA response on NZDF's UFO/UAP reporting practices — clarifies the post-2010 division of responsibility between NZDF and the Civil Aviation Authority.",
                'ag': 'NZDF',
                'cat': 'OIA',
                'date': '2024',
                'u': 'https://www.nzdf.mil.nz/assets/Uploads/DocumentLibrary/OIA-2024-5199-UFO-and-UAP-Reporting.pdf',
                's': 'https://www.nzdf.mil.nz/assets/Uploads/DocumentLibrary/OIA-2024-5199-UFO-and-UAP-Reporting.pdf',
            },
            {
                't': 'CATALOG',
                'ti': 'National Library of NZ — UFO files record',
                'de': "National Library catalog entry for the NZDF UFO file collection — the public-access master record.",
                'ag': 'National Library of NZ',
                'cat': 'Catalog',
                'u': 'https://natlib.govt.nz/records/22979464',
                's': 'https://natlib.govt.nz/records/22979464',
            },
            {
                't': 'CATALOG',
                'ti': 'AIR 1080/6/897 — Kaikoura 1978 file (PDF)',
                'de': "The complete RNZAF file on the 1978 Kaikoura sightings — the most famous unexplained case in NZ aviation history.",
                'ag': 'RNZAF',
                'cat': 'Case File',
                'date': '1978-1981',
                'u': 'https://www.sunrisepage.com/ufo/files/government/NewZealand/AIR-1080-6-897-Volume-1-1978-1981.pdf',
                's': 'https://www.sunrisepage.com/ufo/files/government/NewZealand/AIR-1080-6-897-Volume-1-1978-1981.pdf',
            },
            {
                't': 'CATALOG',
                'ti': 'Archives New Zealand — homepage',
                'de': "Search the full Archway catalog at Archives NZ for AIR 39, AIR 1080, ABFK and related series.",
                'ag': 'Archives NZ',
                'cat': 'Catalog',
                'u': 'https://www.archives.govt.nz/',
                's': 'https://www.archives.govt.nz/',
            },
        ],
        'license': 'Crown copyright — reusable under <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">Creative Commons BY 4.0</a> by default.',
        'source_links': [
            ('archives.govt.nz', 'https://www.archives.govt.nz/'),
            ('nzdf.mil.nz', 'https://www.nzdf.mil.nz/'),
            ('UFOCUS NZ', 'https://ufocusnz.org.nz/'),
        ],
    },
    {
        'slug': 'canada',
        'name': 'Operation Magnet',
        'seal_label': 'CA',
        'super': 'Library &amp; Archives Canada · Dept. of Transport',
        'tone': '#ff6b6b',
        'seal_from': '#ff0000', 'seal_mid': '#990000', 'seal_to': '#330000',
        'bg_tint_a': 'rgba(255,0,0,0.07)', 'bg_tint_b': 'rgba(255,255,255,0.02)',
        'page_title': 'Canada — Operation Magnet · LAC UFO files (Offline Mirror)',
        'meta_desc': "Offline mirror of Canada's UFO records: Wilbert B. Smith's 1950s Operation Magnet at DOT, plus the Library and Archives Canada UFO collection.",
        'og_title': 'Canada — Operation Magnet | realufo.org',
        'og_desc':  "Wilbert B. Smith's 1950s Operation Magnet, Project Second Story (DRB), and the Library and Archives Canada UFO collection — Canada's official UAP record.",
        'og_image': 'https://realufo.org/slideshow/NASA-UAP-VM6-Apollo-17-1972.jpg',
        'coords': '45°25′N, 75°41′W · LIBRARY &amp; ARCHIVES CANADA · OTTAWA',
        'h1_pre':  "Canada's ",
        'h1_em':   'Operation Magnet',
        'h1_post': ' — the first state UFO programme.',
        'hero_html': """
            In <strong>1950</strong>, engineer <strong>Wilbert B. Smith</strong> launched
            Project Magnet at Canada's Department of Transport — the first <em>state-funded</em>
            UFO investigation programme anywhere. <strong>Project Second Story</strong> followed
            at the Defence Research Board. Both their records, plus subsequent RCMP and DND
            files, live at <a href=\"https://library-archives.canada.ca/\" target=\"_blank\" rel=\"noopener\">Library and Archives Canada</a>.
        """,
        'headlines': [
            ('Established', '<span class="h-num">1950</span><div class="h-text">Project Magnet at the Department of Transport.</div>'),
            ('Lead', '<div class="h-text">Wilbert B. Smith — senior radio engineer, DOT.</div>'),
            ('Sister project', '<div class="h-text">Project Second Story · Defence Research Board.</div>'),
            ('Closed', '<span class="h-num">1954</span><div class="h-text">Magnet shuttered; files passed to RCMP / DND.</div>'),
            ('Custodian', '<div class="h-text">Library and Archives Canada · RG 24, RG 18.</div>'),
            ('Famous case', '<div class="h-text">Falcon Lake (1967) · injuries on Stefan Michalak.</div>'),
        ],
        'assets': [
            {
                't': 'CATALOG',
                'ti': 'Library and Archives Canada — UFO research guide',
                'de': "LAC's curated guide to UFO-related records: Project Magnet, Second Story, RCMP files, DND, and individual case folders.",
                'ag': 'Library and Archives Canada',
                'cat': 'Guide',
                'u': 'https://library-archives.canada.ca/eng/collection/research-help/genealogy/Pages/ufos.aspx',
                's': 'https://library-archives.canada.ca/eng/collection/research-help/genealogy/Pages/ufos.aspx',
            },
            {
                't': 'CATALOG',
                'ti': 'LAC — Project Magnet (DOT records, RG 12)',
                'de': "The departmental record group for Project Magnet — Wilbert B. Smith's research files at the Department of Transport.",
                'ag': 'LAC · DOT',
                'cat': 'Record Group',
                'date': '1950-1954',
                'u': 'https://library-archives.canada.ca/eng/collection/research-help/government-canada/Pages/government-canada.aspx',
                's': 'https://library-archives.canada.ca/eng/collection/research-help/government-canada/Pages/government-canada.aspx',
            },
            {
                't': 'CATALOG',
                'ti': 'LAC — Defence Research Board (RG 24)',
                'de': "Defence Research Board records including Project Second Story — Canada's military-side UAP investigation programme of the 1950s.",
                'ag': 'LAC · DRB / DND',
                'cat': 'Record Group',
                'u': 'https://library-archives.canada.ca/',
                's': 'https://library-archives.canada.ca/',
            },
            {
                't': 'CATALOG',
                'ti': 'LAC — RCMP UFO files (RG 18)',
                'de': "Royal Canadian Mounted Police record group includes UFO sighting and investigation files filed alongside other operational records.",
                'ag': 'LAC · RCMP',
                'cat': 'Record Group',
                'u': 'https://library-archives.canada.ca/',
                's': 'https://library-archives.canada.ca/',
            },
            {
                't': 'CATALOG',
                'ti': 'LAC catalog search — UFO',
                'de': "Open search across LAC's full holdings for 'UFO', 'unidentified flying object', 'Project Magnet', etc.",
                'ag': 'LAC',
                'cat': 'Catalog',
                'u': 'https://recherche-collection-search.bac-lac.gc.ca/eng/Home/Search?DataSource=Collection&q=ufo',
                's': 'https://recherche-collection-search.bac-lac.gc.ca/eng/Home/Search?DataSource=Collection&q=ufo',
            },
        ],
        'license': 'Crown copyright — Government of Canada Open Government Licence.',
        'source_links': [
            ('library-archives.canada.ca', 'https://library-archives.canada.ca/'),
        ],
    },
    {
        'slug': 'argentina',
        'name': 'CEFAe',
        'seal_label': 'CEFAe',
        'super': 'Comisión de Estudio de Fenómenos Aeroespaciales',
        'tone': '#74acdf',
        'seal_from': '#74acdf', 'seal_mid': '#3d6a9c', 'seal_to': '#1e3a5e',
        'bg_tint_a': 'rgba(116,172,223,0.08)', 'bg_tint_b': 'rgba(255,255,255,0.03)',
        'page_title': 'CEFAe — Argentine Air Force UAP Commission (Offline Mirror)',
        'meta_desc': "Offline mirror of Argentina's CEFAe — the Fuerza Aérea Argentina's UAP investigation commission since 2011.",
        'og_title': 'CEFAe — Argentina | realufo.org',
        'og_desc':  "Argentina's Comisión de Estudio de Fenómenos Aeroespaciales (CEFAe) — the Fuerza Aérea Argentina's official UAP investigation arm since 2011.",
        'og_image': 'https://realufo.org/slideshow/NASA-UAP-VM6-Apollo-17-1972.jpg',
        'coords': '34°36′S, 58°22′W · FUERZA AÉREA ARGENTINA · BUENOS AIRES',
        'h1_pre':  "Argentina's ",
        'h1_em':   'CEFAe',
        'h1_post': ' — Air Force commission, since 2011.',
        'hero_html': """
            <strong>CEFAe</strong> (Comisión de Estudio de Fenómenos Aeroespaciales) is the
            Fuerza Aérea Argentina's official UAP body, formed in <strong>2011</strong>
            under the Ministerio de Defensa. Operates inside the Air Force; investigates
            reports from pilots, ATC, and the public; publishes findings via FAA's institutional
            channels. Records are accessible via <a href=\"https://www.argentina.gob.ar/fuerzaaerea\" target=\"_blank\" rel=\"noopener\">argentina.gob.ar/fuerzaaerea</a>.
        """,
        'headlines': [
            ('Founded', '<span class="h-num">2011</span><div class="h-text">By order of the Ministerio de Defensa.</div>'),
            ('Parent', '<div class="h-text">Fuerza Aérea Argentina · Comando de Operaciones.</div>'),
            ('Mandate', '<div class="h-text">Investigate aerospatial-phenomenon reports from pilots, ATC, the public.</div>'),
            ('Output', '<div class="h-text">Case files, findings, periodic statements via FAA channels.</div>'),
            ('Authority', '<div class="h-text">Ministerio de Defensa de la Nación.</div>'),
            ('Status', '<div class="h-text">Active.</div>'),
        ],
        'assets': [
            {
                't': 'CATALOG',
                'ti': 'Fuerza Aérea Argentina — official site',
                'de': "FAA's institutional site. CEFAe announcements and statements are published through the FAA's news channel rather than a dedicated portal.",
                'ag': 'Fuerza Aérea Argentina',
                'cat': 'Catalog',
                'u': 'https://www.argentina.gob.ar/fuerzaaerea',
                's': 'https://www.argentina.gob.ar/fuerzaaerea',
            },
            {
                't': 'CATALOG',
                'ti': 'Ministerio de Defensa — Argentine national defence',
                'de': "Parent ministry. Defence-policy publications and CEFAe-related ministerial decrees are filed here.",
                'ag': 'Ministerio de Defensa',
                'cat': 'Catalog',
                'u': 'https://www.argentina.gob.ar/defensa',
                's': 'https://www.argentina.gob.ar/defensa',
            },
            {
                't': 'CATALOG',
                'ti': 'Archivo General de la Nación — Argentina',
                'de': "Argentina's national archives — host CEFAe and earlier Air Force records about aerospatial phenomena.",
                'ag': 'Archivo General de la Nación',
                'cat': 'Catalog',
                'u': 'https://www.argentina.gob.ar/interior/archivo',
                's': 'https://www.argentina.gob.ar/interior/archivo',
            },
        ],
        'license': 'Public-sector works reusable under Ley 27.275 (acceso a la información pública).',
        'source_links': [
            ('argentina.gob.ar/fuerzaaerea', 'https://www.argentina.gob.ar/fuerzaaerea'),
            ('Ministerio de Defensa', 'https://www.argentina.gob.ar/defensa'),
        ],
    },
    {
        'slug': 'uruguay',
        'name': 'CRIDOVNI',
        'seal_label': 'UY',
        'super': 'Comisión Receptora e Investigadora de Denuncias de OVNI',
        'tone': '#3ba0d8',
        'seal_from': '#3ba0d8', 'seal_mid': '#1e5d80', 'seal_to': '#0d2c3e',
        'bg_tint_a': 'rgba(59,160,216,0.08)', 'bg_tint_b': 'rgba(255,255,255,0.03)',
        'page_title': 'CRIDOVNI — Uruguay Air Force UFO Commission (Offline Mirror)',
        'meta_desc': "Offline mirror of CRIDOVNI — Uruguay's UFO investigation commission, world's oldest continuously-operating state UAP programme (1979→).",
        'og_title': 'CRIDOVNI — Uruguay | realufo.org',
        'og_desc':  "Uruguay's CRIDOVNI — the world's oldest continuously-operating state UFO programme. Founded 1979 inside the Fuerza Aérea Uruguaya.",
        'og_image': 'https://realufo.org/slideshow/NASA-UAP-VM6-Apollo-17-1972.jpg',
        'coords': '34°54′S, 56°10′W · FUERZA AÉREA URUGUAYA · MONTEVIDEO',
        'h1_pre':  "Uruguay's ",
        'h1_em':   'CRIDOVNI',
        'h1_post': ' — oldest continuously-running UFO office.',
        'hero_html': """
            <strong>CRIDOVNI</strong> (Comisión Receptora e Investigadora de Denuncias de OVNI)
            was established in <strong>1979</strong> inside Uruguay's Air Force — the
            <em>world's oldest continuously-operating</em> state UAP programme. Receives reports
            from pilots and the public, investigates with a scientific framework, and maintains a
            classified case archive of nearly five decades of Uruguayan sightings.
            Source: <a href=\"https://www.fau.mil.uy/\" target=\"_blank\" rel=\"noopener\">fau.mil.uy</a>.
        """,
        'headlines': [
            ('Founded', '<span class="h-num">1979</span><div class="h-text">By Air Force resolution — under Fuerza Aérea Uruguaya.</div>'),
            ('Tenure', '<div class="h-text"><strong>45+ years</strong> — longest continuously-operating in the world.</div>'),
            ('Estimate', '<div class="h-text">~2,000 reports investigated since founding (FAU public statements).</div>'),
            ('Resolution', '<div class="h-text"><strong>~40%</strong> remain unexplained after investigation (FAU figure).</div>'),
            ('Parent', '<div class="h-text">Fuerza Aérea Uruguaya · Comando General.</div>'),
            ('Status', '<div class="h-text">Active.</div>'),
        ],
        'assets': [
            {
                't': 'CATALOG',
                'ti': 'Fuerza Aérea Uruguaya — homepage',
                'de': "FAU's institutional site. CRIDOVNI announcements appear here as press releases rather than on a dedicated portal.",
                'ag': 'FAU',
                'cat': 'Catalog',
                'u': 'https://www.fau.mil.uy/',
                's': 'https://www.fau.mil.uy/',
            },
            {
                't': 'CATALOG',
                'ti': 'Ministerio de Defensa Nacional — Uruguay',
                'de': "Parent ministry — Defence-policy publications and CRIDOVNI-related ministerial communiqués.",
                'ag': 'Ministerio de Defensa Nacional',
                'cat': 'Catalog',
                'u': 'https://www.gub.uy/ministerio-defensa-nacional/',
                's': 'https://www.gub.uy/ministerio-defensa-nacional/',
            },
            {
                't': 'CATALOG',
                'ti': 'Archivo General de la Nación — Uruguay',
                'de': "Uruguay's national archive — long-term custodian of CRIDOVNI and FAU records once declassified.",
                'ag': 'AGN',
                'cat': 'Catalog',
                'u': 'https://www.gub.uy/archivo-general-nacion/',
                's': 'https://www.gub.uy/archivo-general-nacion/',
            },
        ],
        'license': 'Reusable under Ley nº 18.381 (acceso a la información pública).',
        'source_links': [
            ('fau.mil.uy', 'https://www.fau.mil.uy/'),
            ('gub.uy', 'https://www.gub.uy/'),
        ],
    },
    {
        'slug': 'peru',
        'name': 'OIFAA',
        'seal_label': 'OIFAA',
        'super': 'Oficina de Investigación de Fenómenos Aéreos Anómalos · FAP',
        'tone': '#ff6b6b',
        'seal_from': '#d91023', 'seal_mid': '#7d0b14', 'seal_to': '#3a0508',
        'bg_tint_a': 'rgba(217,16,35,0.07)', 'bg_tint_b': 'rgba(255,255,255,0.03)',
        'page_title': 'OIFAA — Peruvian Air Force UAP Office (Offline Mirror)',
        'meta_desc': "Offline mirror of Peru's OIFAA — Fuerza Aérea del Perú's anomalous aerial phenomena investigation office, reactivated 2022.",
        'og_title': 'OIFAA — Peru | realufo.org',
        'og_desc':  "Peru's Oficina de Investigación de Fenómenos Aéreos Anómalos (OIFAA), reactivated 2022 inside the Fuerza Aérea del Perú.",
        'og_image': 'https://realufo.org/slideshow/NASA-UAP-VM6-Apollo-17-1972.jpg',
        'coords': '12°02′S, 77°02′W · FUERZA AÉREA DEL PERÚ · LIMA',
        'h1_pre':  "Peru's ",
        'h1_em':   'OIFAA',
        'h1_post': ' — reactivated 2022 under the Air Force.',
        'hero_html': """
            <strong>OIFAA</strong> (Oficina de Investigación de Fenómenos Aéreos Anómalos)
            is the Fuerza Aérea del Perú's UAP investigation office. Originally founded in
            <strong>2001</strong>, deactivated, then <strong>reactivated in 2022</strong> by
            FAP directive. Receives reports from pilots, ATC and the public; cross-correlates
            with radar / satellite data. Sources: <a href=\"https://www.fap.mil.pe/\" target=\"_blank\" rel=\"noopener\">fap.mil.pe</a>.
        """,
        'headlines': [
            ('First founded', '<span class="h-num">2001</span><div class="h-text">By order of the Comandancia General FAP.</div>'),
            ('Reactivated', '<span class="h-num">2022</span><div class="h-text">After period of dormancy.</div>'),
            ('Parent', '<div class="h-text">Fuerza Aérea del Perú · Comando de Operaciones.</div>'),
            ('Mandate', '<div class="h-text">Aerospatial-phenomena investigation; scientific framework.</div>'),
            ('Reporting', '<div class="h-text">Channels: pilot reports · ATC · civilian denuncias.</div>'),
            ('Status', '<div class="h-text">Active.</div>'),
        ],
        'assets': [
            {
                't': 'CATALOG',
                'ti': 'Fuerza Aérea del Perú — official site',
                'de': "FAP's institutional site. OIFAA reactivation announcement and subsequent communiqués are published here.",
                'ag': 'FAP',
                'cat': 'Catalog',
                'u': 'https://www.fap.mil.pe/',
                's': 'https://www.fap.mil.pe/',
            },
            {
                't': 'CATALOG',
                'ti': 'Ministerio de Defensa del Perú',
                'de': "Parent ministry. OIFAA-related ministerial decrees and policy publications are filed here.",
                'ag': 'Ministerio de Defensa',
                'cat': 'Catalog',
                'u': 'https://www.gob.pe/mindef',
                's': 'https://www.gob.pe/mindef',
            },
            {
                't': 'CATALOG',
                'ti': 'Archivo General de la Nación — Perú',
                'de': "Peru's national archives. Long-term custodian of declassified FAP records including those produced by OIFAA.",
                'ag': 'AGN Perú',
                'cat': 'Catalog',
                'u': 'https://www.gob.pe/agn',
                's': 'https://www.gob.pe/agn',
            },
        ],
        'license': 'Reusable under Ley 27.806 (Acceso a la información pública).',
        'source_links': [
            ('fap.mil.pe', 'https://www.fap.mil.pe/'),
            ('Ministerio de Defensa', 'https://www.gob.pe/mindef'),
        ],
    },
    {
        'slug': 'spain',
        'name': 'Ejército del Aire',
        'seal_label': 'ES',
        'super': 'Ejército del Aire y del Espacio · España',
        'tone': '#f4c542',
        'seal_from': '#aa151b', 'seal_mid': '#700c10', 'seal_to': '#350608',
        'bg_tint_a': 'rgba(170,21,27,0.07)', 'bg_tint_b': 'rgba(244,197,66,0.04)',
        'page_title': 'Spain — Ejército del Aire declassified UFO archive (Offline Mirror)',
        'meta_desc': "Offline mirror of Spain's declassified Air Force UFO archive — 1,900 pages, 86 cases, released 1992-1999 under General Alfredo Chamorro Chapinal.",
        'og_title': 'Ejército del Aire — Spain | realufo.org',
        'og_desc':  "Spain's declassified Air Force UFO archive — 86 cases, ~1,900 pages, 1962-1995. Released over 1992-1999 by Mando Operativo Aéreo.",
        'og_image': 'https://realufo.org/slideshow/NASA-UAP-VM6-Apollo-17-1972.jpg',
        'coords': '40°25′N, 3°43′W · CUARTEL GENERAL DEL AIRE · MADRID',
        'h1_pre':  "Spain's ",
        'h1_em':   'pioneering',
        'h1_post': ' Air Force declassification.',
        'hero_html': """
            Between <strong>1992 and 1999</strong>, Spain's Ejército del Aire became one of the
            <em>first NATO air forces</em> to systematically declassify its UFO archive.
            <strong>86 case files · ~1,900 pages</strong> spanning <strong>1962-1995</strong>
            were released under General <strong>Alfredo Chamorro Chapinal</strong>. The
            files are held at the Archivo Histórico del Ejército del Aire. Source: <a href=\"https://ejercitodelaire.defensa.gob.es/\" target=\"_blank\" rel=\"noopener\">ejercitodelaire.defensa.gob.es</a>.
        """,
        'headlines': [
            ('Declassified', '<span class="h-num">1992-1999</span><div class="h-text">Over 7 years — gradual case-by-case release.</div>'),
            ('Cases', '<span class="h-num">86</span><div class="h-text">Investigated files spanning 1962-1995.</div>'),
            ('Pages', '<span class="h-num">~1 900</span><div class="h-text">Field reports, radar tracks, witness statements.</div>'),
            ('Lead', '<div class="h-text">Gen. Alfredo Chamorro Chapinal · Mando Operativo Aéreo.</div>'),
            ('Status', '<div class="h-text">Programme concluded 1999; files at Archivo Histórico.</div>'),
            ('Authority', '<div class="h-text">Ministerio de Defensa de España.</div>'),
        ],
        'assets': [
            {
                't': 'CATALOG',
                'ti': 'Ejército del Aire y del Espacio — homepage',
                'de': "Official site of Spain's air force. Archive-access requests + declassified-file viewing logistics are described here.",
                'ag': 'Ejército del Aire',
                'cat': 'Catalog',
                'u': 'https://ejercitodelaire.defensa.gob.es/',
                's': 'https://ejercitodelaire.defensa.gob.es/',
            },
            {
                't': 'CATALOG',
                'ti': 'Archivo Histórico del Ejército del Aire',
                'de': "Historical archive holding the declassified UFO files (Madrid). On-site access by appointment.",
                'ag': 'Ejército del Aire',
                'cat': 'Archive',
                'u': 'https://ejercitodelaire.defensa.gob.es/EA/ejercitodelaire/es/organizacion/archivo-historico/',
                's': 'https://ejercitodelaire.defensa.gob.es/EA/ejercitodelaire/es/organizacion/archivo-historico/',
            },
            {
                't': 'CATALOG',
                'ti': 'Ministerio de Defensa — Portal de la Cultura de Defensa',
                'de': "Spain's defence culture portal — historical research guides including the Air Force collection.",
                'ag': 'Ministerio de Defensa',
                'cat': 'Catalog',
                'u': 'https://www.defensa.gob.es/portalcultura/',
                's': 'https://www.defensa.gob.es/portalcultura/',
            },
        ],
        'license': 'Reusable under Ley 19/2013 sobre transparencia y acceso a la información pública.',
        'source_links': [
            ('ejercitodelaire.defensa.gob.es', 'https://ejercitodelaire.defensa.gob.es/'),
            ('defensa.gob.es', 'https://www.defensa.gob.es/'),
        ],
    },
    {
        'slug': 'italy',
        'name': 'Aeronautica Militare',
        'seal_label': 'AM',
        'super': 'Aeronautica Militare Italiana · Stato Maggiore',
        'tone': '#5cb85c',
        'seal_from': '#009246', 'seal_mid': '#005a2b', 'seal_to': '#002612',
        'bg_tint_a': 'rgba(0,146,70,0.07)', 'bg_tint_b': 'rgba(206,43,55,0.03)',
        'page_title': 'Italy — Aeronautica Militare UFO archive (Offline Mirror)',
        'meta_desc': "Offline mirror of Italy's Aeronautica Militare UFO records — Reparto Generale Sicurezza Stato Maggiore Aeronautica declassifications since 2008.",
        'og_title': 'Aeronautica Militare — Italy | realufo.org',
        'og_desc':  "Italy's Aeronautica Militare UFO archive — declassified by Stato Maggiore Aeronautica from 2008 onward via the Sicurezza Aerea web portal.",
        'og_image': 'https://realufo.org/slideshow/NASA-UAP-VM6-Apollo-17-1972.jpg',
        'coords': '41°54′N, 12°29′E · STATO MAGGIORE AERONAUTICA · ROMA',
        'h1_pre':  "Italy's ",
        'h1_em':   'Aeronautica Militare',
        'h1_post': ' — UAP records since 1933.',
        'hero_html': """
            Italy's <strong>Aeronautica Militare</strong> has investigated aerial phenomena since
            <strong>1933</strong> — the longest unbroken state interest worldwide. Since
            <strong>2008</strong>, the Stato Maggiore Aeronautica has systematically declassified
            UFO case files via the <strong>Sicurezza Aerea</strong> portal. Records spread across
            Aeronautica Militare archives and ufficio statistica.
            Source: <a href=\"https://www.aeronautica.difesa.it/\" target=\"_blank\" rel=\"noopener\">aeronautica.difesa.it</a>.
        """,
        'headlines': [
            ('First files', '<span class="h-num">1933</span><div class="h-text">Earliest Italian Air Force UFO-style records.</div>'),
            ('Public release', '<span class="h-num">2008</span><div class="h-text">Stato Maggiore Aeronautica begins online publication.</div>'),
            ('Custodian', '<div class="h-text">Aeronautica Militare · Stato Maggiore — Sicurezza Aerea.</div>'),
            ('Format', '<div class="h-text">Per-case PDFs published under Riservato &rarr; Disclassificato.</div>'),
            ('Decades', '<div class="h-text">Cases organised by year groupings 1979 → present.</div>'),
            ('Status', '<div class="h-text">Active; new cases published on a rolling basis.</div>'),
        ],
        'assets': [
            {
                't': 'CATALOG',
                'ti': 'Aeronautica Militare — official site',
                'de': "Italy's Air Force institutional site. UFO file releases are published through the Sicurezza Aerea sub-portal.",
                'ag': 'Aeronautica Militare',
                'cat': 'Catalog',
                'u': 'https://www.aeronautica.difesa.it/',
                's': 'https://www.aeronautica.difesa.it/',
            },
            {
                't': 'CATALOG',
                'ti': 'Stato Maggiore Aeronautica — UFO portal',
                'de': "Stato Maggiore's dedicated UFO/UAP section listing declassified case files by year.",
                'ag': 'Stato Maggiore Aeronautica',
                'cat': 'Catalog',
                'u': 'https://www.aeronautica.difesa.it/comunicazione/UFO/',
                's': 'https://www.aeronautica.difesa.it/comunicazione/UFO/',
            },
            {
                't': 'CATALOG',
                'ti': 'Ministero della Difesa — Italy',
                'de': "Parent ministry. Defence-policy publications and UFO-related ministerial communiqués are archived here.",
                'ag': 'Ministero della Difesa',
                'cat': 'Catalog',
                'u': 'https://www.difesa.it/',
                's': 'https://www.difesa.it/',
            },
            {
                't': 'CATALOG',
                'ti': 'Archivio Centrale dello Stato — Italy',
                'de': "Italy's central state archive — long-term custodian of declassified Air Force files including UFO records.",
                'ag': 'Archivio Centrale dello Stato',
                'cat': 'Catalog',
                'u': 'https://acs.cultura.gov.it/',
                's': 'https://acs.cultura.gov.it/',
            },
        ],
        'license': 'Reusable under D.lgs. 33/2013 (decreto trasparenza).',
        'source_links': [
            ('aeronautica.difesa.it', 'https://www.aeronautica.difesa.it/'),
            ('difesa.it', 'https://www.difesa.it/'),
        ],
    },
]

# All-mirror nav list (used in every header + footer)
ALL_MIRRORS = [
    ('war.gov', '../index.html'),
    ('AARO',    '../aaro-mirror/index.html'),
    ('NASA',    '../nasa-mirror/index.html'),
    ('NARA',    '../nara-mirror/index.html'),
    ('GEIPAN',  '../geipan-mirror/index.html'),
    ('UK',      '../uk-mirror/index.html'),
    ('Brazil',  '../brazil-mirror/index.html'),
    ('Chile',   '../chile-mirror/index.html'),
    ('NZ',      '../nz-mirror/index.html'),
    ('Canada',  '../canada-mirror/index.html'),
    ('Argentina','../argentina-mirror/index.html'),
    ('Uruguay', '../uruguay-mirror/index.html'),
    ('Peru',    '../peru-mirror/index.html'),
    ('Spain',   '../spain-mirror/index.html'),
    ('Italy',   '../italy-mirror/index.html'),
]


def write_favicon(slug, label, c1, c2, c3, dark_text=False):
    text_fill = '#0a0a0c' if dark_text else '#e8e3d8'
    p = os.path.join(REPO, f'{slug}-mirror', 'assets', 'favicon.svg')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w').write(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <radialGradient id="g" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="60%" stop-color="{c2}"/>
      <stop offset="100%" stop-color="{c3}"/>
    </radialGradient>
  </defs>
  <rect width="64" height="64" fill="#0a0a0c"/>
  <circle cx="32" cy="32" r="26" fill="url(#g)" stroke="#e8e3d8" stroke-width="2"/>
  <circle cx="32" cy="32" r="20" fill="none" stroke="#e8e3d8" stroke-width="1" stroke-dasharray="2 2" opacity="0.5"/>
  <text x="32" y="37" font-family="ui-monospace,Consolas,monospace" font-size="{10 if len(label)<=4 else 9}" font-weight="700" text-anchor="middle" fill="{text_fill}" letter-spacing="-0.3">{label}</text>
</svg>
''')


def git_tracked(mirror_slug, sub):
    try:
        out = subprocess.run(['git','-C',REPO,'ls-files',f'{mirror_slug}-mirror/{sub}/'],
            capture_output=True, text=True, check=True).stdout
        prefix = f'{mirror_slug}-mirror/{sub}/'
        return {ln[len(prefix):] for ln in out.splitlines() if ln.startswith(prefix)}
    except Exception:
        p = os.path.join(REPO, f'{mirror_slug}-mirror', sub)
        return set(os.listdir(p)) if os.path.isdir(p) else set()


def build_mirror(cfg):
    slug = cfg['slug']
    root = os.path.join(REPO, f'{slug}-mirror')
    os.makedirs(root, exist_ok=True)

    write_favicon(slug, cfg['seal_label'], cfg['seal_from'], cfg['seal_mid'], cfg['seal_to'])

    # Filter out this mirror's self-link in nav.
    nav_html = '\n'.join(
        f'        <li><a href="{href.replace("../", "../"+slug+"-mirror/" if href.endswith("index.html") and "/{slug}-mirror/" in href else "../")}">{label}</a></li>'
        for label, href in ALL_MIRRORS
        if not href.endswith(f'/{slug}-mirror/index.html')
    )
    # Simpler: just emit all and let the self-link be a no-op anchor.
    nav_lines = []
    for label, href in ALL_MIRRORS:
        if href.endswith(f'/{slug}-mirror/index.html'):
            continue
        nav_lines.append(f'        <li><a href="{href}">{label}</a></li>')
    nav_html = '\n'.join(nav_lines)

    headlines_html = '\n      '.join(
        f'<div class="head-card"><div class="h-label">{label}</div>{html}</div>'
        for label, html in cfg['headlines']
    )

    source_links_html = '\n        '.join(
        f'<li><a href="{href}" target="_blank" rel="noopener">{label} ↗</a></li>'
        for label, href in cfg['source_links']
    )

    stats = {
        'total': len(cfg['assets']),
        'local_total': sum(1 for a in cfg['assets'] if a.get('l')),
        'pdf_total': sum(1 for a in cfg['assets'] if a['t'] == 'PDF'),
        'catalog_total': sum(1 for a in cfg['assets'] if a['t'] == 'CATALOG'),
    }
    data_json = json.dumps({'assets': cfg['assets'], 'stats': stats}, ensure_ascii=False).replace('</script', '<\\/script')

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{cfg['page_title']}</title>
<meta name="description" content="{cfg['meta_desc']}">
<link rel="canonical" href="https://realufo.org/{slug}-mirror/">
<meta property="og:title" content="{cfg['og_title']}">
<meta property="og:description" content="{cfg['og_desc']}">
<meta property="og:image" content="{cfg['og_image']}">
<meta property="og:url" content="https://realufo.org/{slug}-mirror/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="realufo.org">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{cfg['og_title']}">
<meta name="twitter:description" content="{cfg['og_desc']}">
<meta name="twitter:image" content="{cfg['og_image']}">
<link rel="icon" type="image/svg+xml" href="./assets/favicon.svg">
<link rel="apple-touch-icon" href="./assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet">
<style>
{SHARED_CSS}
:root {{ --caution: {cfg['tone']}; }}
.seal {{ background: radial-gradient(circle at 50% 50%, {cfg['seal_from']}, {cfg['seal_mid']} 60%, {cfg['seal_to']}); }}
body {{ background-image:
  radial-gradient(ellipse at 20% 0%, {cfg['bg_tint_a']} 0%, transparent 50%),
  radial-gradient(ellipse at 80% 100%, {cfg['bg_tint_b']} 0%, transparent 50%); background-attachment: fixed; }}
</style>
</head>
<body>
<div class="scanlines"></div>

<div class="header-wrap">
<header>
  <div class="container">
    <a href="#top" class="brand">
      <div class="seal">{cfg['seal_label']}</div>
      <div class="brand-text">
        <span class="super">{cfg['super']}</span>
        <span class="name">{cfg['name']}</span>
      </div>
    </a>
    <button class="nav-toggle" id="nav-toggle" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>
    <nav class="primary" id="primary-nav">
      <ul>
        <li><a href="#top">Intro</a></li>
        <li><a href="#headlines">Headlines</a></li>
        <li><a href="#archive" class="active">Records</a></li>
{nav_html}
      </ul>
    </nav>
  </div>
</header>
</div>

<div class="hero" id="top">
  <div class="container">
    <div class="coords">{cfg['coords']}</div>
    <h1 class="hero-title">{cfg['h1_pre']}<em>{cfg['h1_em']}</em>{cfg['h1_post']}</h1>
    <p class="hero-sub">{cfg['hero_html'].strip()}</p>
  </div>
</div>

<section id="headlines" class="headlines">
  <div class="container">
    <div class="section-label">§ Headlines · {cfg['name']}, distilled</div>
    <div class="head-grid">
      {headlines_html}
    </div>
  </div>
</section>

<section id="archive">
  <div class="container">
    <div class="section-label">§ Records · Catalog gateways</div>
    <h2>Every official entry-point.</h2>
    <p class="lede">
      Cards below deep-link into the official catalogs and institutional pages. Where direct PDFs
      were reachable they're mirrored locally; everything else opens on the live source.
    </p>

    <div class="stats-grid" id="arch-stats"></div>

    <div class="arch-controls-bar">
      <div class="tabs" id="arch-tabs"></div>
      <div class="search-wrap">
        <input id="arch-search" type="search" placeholder="Search title, agency, date…" autocomplete="off">
      </div>
    </div>

    <div class="arch-grid" id="arch-grid"></div>
    <div class="empty" id="arch-empty" hidden>No records match.</div>
  </div>
</section>

<footer>
  <div class="container">
    <div>
      <h4>{cfg['name']} Mirror</h4>
      <p style="color: var(--ink-dim); font-family: var(--serif); margin-bottom: 14px;">
        Offline gateway to {cfg['name']}. {cfg['license']}
      </p>
      <p style="color: var(--ink-faint); font-size: 10px; letter-spacing: 0.1em;">Captured for realufo.org · 2026.</p>
    </div>
    <div>
      <h4>Related Mirrors</h4>
      <ul>
        <li><a href="../index.html">war.gov / UFO Release 01</a></li>
        <li><a href="../aaro-mirror/index.html">AARO — DoW</a></li>
        <li><a href="../nasa-mirror/index.html">NASA UAP Study</a></li>
        <li><a href="../nara-mirror/index.html">NARA UAP Records</a></li>
        <li><a href="../geipan-mirror/index.html">France GEIPAN</a></li>
        <li><a href="../uk-mirror/index.html">UK MoD UFO Files</a></li>
        <li><a href="../brazil-mirror/index.html">Brazil OVNI</a></li>
        <li><a href="../chile-mirror/index.html">Chile SEFAA</a></li>
      </ul>
    </div>
    <div>
      <h4>Source</h4>
      <ul>
        {source_links_html}
      </ul>
    </div>
    <div class="colophon">
      <span>Offline mirror · For research and reference</span>
      <span>realufo.org</span>
    </div>
  </div>
</footer>

<div class="lightbox" id="lightbox" aria-hidden="true">
  <div class="lb-close" id="lb-close">×</div>
  <button class="lb-nav prev" id="lb-prev" aria-label="Previous (←)">‹</button>
  <button class="lb-nav next" id="lb-next" aria-label="Next (→)">›</button>
  <div class="lb-counter" id="lb-counter"></div>
  <div class="lb-inner" id="lb-inner"></div>
</div>

<script id="arch-data" type="application/json">{data_json}</script>
<script>{SHARED_JS}</script>
</body>
</html>
'''
    open(os.path.join(root, 'index.html'), 'w', encoding='utf-8').write(page)
    print(f'  {slug:10s}  → index.html  ({len(page):,} B)  {stats["local_total"]}/{stats["total"]} local')


print('Building 7 mirrors:')
for cfg in CONFIG:
    build_mirror(cfg)
print('done.')
