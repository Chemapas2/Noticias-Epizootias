import base64
import html
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from io import BytesIO

import streamlit as st


# =========================================================
# CONFIGURACIÓN
# =========================================================
APP_TITLE = "Noticias Epizootias"
AUTO_REFRESH = "5m"
DEFAULT_MAX_NEWS_PER_DISEASE = 5
DEFAULT_DAYS_BACK = 7
MIN_DAYS_BACK = 1
MAX_DAYS_BACK = 60
TIMEOUT_SECONDS = 20

# Archivos de marca esperados en la misma carpeta que main.py
NUTRECO_LOGO_PATH = "Logo Nutreco.jpg"
TECHTEAM_LOGO_PATH = "Logo TechTeam 2.jpg"
PINK_BANNER_PATH = "Solapa rosa trasparente.png"

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=es&gl=ES&ceid=ES:es"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NoticiasEpizootias/2.0; +https://github.com/)"
}

REGION_TERMS = [
    "españa",
    "espana",
    "portugal",
    "europa",
    "europeo",
    "europea",
    "union europea",
    "unión europea",
    "ue",
    "iberia",
    "ibérico",
    "iberico",
    "península ibérica",
    "peninsula iberica",
]

DISEASES = {
    "DNC - Dermatitis Nodular Contagiosa": {
        "queries": [
            '"dermatitis nodular contagiosa" (vacuno OR bovino) (España OR Portugal OR Europa OR UE OR "Unión Europea")',
            '"lumpy skin disease" (vacuno OR bovino) (España OR Portugal OR Europa OR UE OR "Unión Europea")',
            'DNC vacuno (España OR Portugal OR Europa OR UE)',
        ],
        "match_terms": [
            "dermatitis nodular contagiosa",
            "lumpy skin disease",
            "lumpy skin",
            "dnc",
        ],
        "report_color": "#0b3b7a",
    },
    "IAAP - Influenza Aviar": {
        "queries": [
            '("influenza aviar" OR "gripe aviar" OR IAAP OR HPAI) (aves OR aviar OR poultry) (España OR Portugal OR Europa OR UE OR "Unión Europea")',
            '"influenza aviar altamente patógena" (España OR Portugal OR Europa OR UE)',
            '"gripe aviar" (España OR Portugal OR Europa OR UE)',
        ],
        "match_terms": [
            "influenza aviar",
            "gripe aviar",
            "iaap",
            "hpai",
        ],
        "report_color": "#c10075",
    },
    "PPA - Peste Porcina Africana": {
        "queries": [
            '("peste porcina africana" OR PPA OR ASF) (porcino OR cerdo OR cerdos OR jabalí OR jabalies OR jabalíes) (España OR Portugal OR Europa OR UE OR "Unión Europea")',
            '"peste porcina africana" (España OR Portugal OR Europa OR UE)',
            'PPA porcino (España OR Portugal OR Europa OR UE)',
        ],
        "match_terms": [
            "peste porcina africana",
            "ppa",
            "asf",
        ],
        "report_color": "#f28c00",
    },
    "EN - Enfermedad de Newcastle": {
        "queries": [
            '("enfermedad de Newcastle" OR Newcastle) (aves OR aviar OR poultry) (España OR Portugal OR Europa OR UE OR "Unión Europea")',
            '"newcastle disease" (aves OR aviar OR poultry) (España OR Portugal OR Europa OR UE OR "Unión Europea")',
            'Newcastle aviar (España OR Portugal OR Europa OR UE)',
        ],
        "match_terms": [
            "enfermedad de newcastle",
            "newcastle disease",
            "newcastle",
        ],
        "report_color": "#4b9f47",
    },
}


# =========================================================
# UTILIDADES DE MARCA
# =========================================================
def guess_mime_type(path: str) -> str:
    ext = os.path.splitext(path.lower())[1]
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    return "image/jpeg"


@st.cache_data(show_spinner=False)
def image_to_data_uri(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{guess_mime_type(path)};base64,{encoded}"


def load_image_bytes(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def inject_brand_css():
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.0rem;
                padding-bottom: 2rem;
                max-width: 1350px;
            }

            .brand-title {
                font-size: 2.2rem;
                font-weight: 800;
                color: #0b3b7a;
                margin-top: 0.30rem;
                margin-bottom: 0.10rem;
            }

            .brand-subtitle {
                font-size: 1rem;
                color: #444444;
                margin-bottom: 0.35rem;
            }

            .brand-note {
                font-size: 0.92rem;
                color: #666666;
                margin-bottom: 1rem;
            }

            div.stButton > button,
            div.stDownloadButton > button {
                border-radius: 12px;
                border: 1px solid #c10075;
            }

            div[data-testid="stMetric"] {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(128,128,128,0.18);
                padding: 12px;
                border-radius: 14px;
            }

            .report-preview {
                border: 1px solid rgba(128,128,128,0.20);
                border-radius: 14px;
                padding: 14px 16px;
                background: rgba(255,255,255,0.02);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_header():
    banner_uri = image_to_data_uri(PINK_BANNER_PATH)
    if banner_uri:
        st.markdown(
            f"""
            <div style="margin-bottom: 0.35rem;">
                <img src="{banner_uri}" style="width: 100%; border-radius: 10px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns([3.8, 1.4])

    with col1:
        if os.path.exists(NUTRECO_LOGO_PATH):
            st.image(NUTRECO_LOGO_PATH, use_container_width=True)

    with col2:
        if os.path.exists(TECHTEAM_LOGO_PATH):
            st.image(TECHTEAM_LOGO_PATH, width=185)

    st.markdown(f'<div class="brand-title">{APP_TITLE}</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="brand-subtitle">
            Monitor automático en Streamlit de DNC, IAAP, PPA y Enfermedad de Newcastle en medios en español.
        </div>
        <div class="brand-note">
            Cobertura orientada a noticias sobre España, Portugal y Europa, con posibilidad de seleccionar noticias y generar un informe HTML con enlaces, resumen y fuentes.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# UTILIDADES DE DATOS
# =========================================================
def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def text_to_key(text: str) -> str:
    text = normalize_text(text).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_date(date_str: str):
    if not date_str:
        return None
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def format_dt(dt: datetime) -> str:
    if not dt:
        return "Fecha no disponible"
    return dt.astimezone().strftime("%d/%m/%Y %H:%M")


def time_ago(dt: datetime) -> str:
    if not dt:
        return ""
    now = datetime.now(timezone.utc)
    delta = now - dt
    minutes = int(delta.total_seconds() // 60)
    hours = int(delta.total_seconds() // 3600)
    days = delta.days

    if minutes < 60:
        return f"hace {minutes} min"
    if hours < 24:
        return f"hace {hours} h"
    return f"hace {days} d"


def build_rss_url(query: str) -> str:
    return GOOGLE_NEWS_RSS.format(query=urllib.parse.quote(query, safe=""))


def build_queries(base_queries, days_back: int):
    return [f"{q} when:{days_back}d" for q in base_queries]


def fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", errors="ignore")


def xml_item_to_dict(item) -> dict:
    title = normalize_text(item.findtext("title", default=""))
    link = normalize_text(item.findtext("link", default=""))
    pub_date_raw = item.findtext("pubDate", default="")
    description = normalize_text(item.findtext("description", default=""))
    source_elem = item.find("source")
    source = normalize_text(source_elem.text if source_elem is not None else "")

    return {
        "title": title,
        "link": link,
        "published": parse_date(pub_date_raw),
        "published_raw": pub_date_raw,
        "description": description,
        "source": source or "Medio no identificado",
    }


def contains_region(text: str) -> bool:
    t = text_to_key(text)
    return any(term in t for term in REGION_TERMS)


def contains_disease(text: str, disease_terms) -> bool:
    t = text_to_key(text)
    return any(term in t for term in disease_terms)


def is_recent(dt: datetime, days_back: int) -> bool:
    if not dt:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    return dt >= cutoff


def deduplicate_news(items):
    seen = set()
    unique = []
    for item in items:
        key = (
            text_to_key(item.get("title", "")),
            text_to_key(item.get("source", "")),
            text_to_key(item.get("link", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def sort_news(items):
    return sorted(
        items,
        key=lambda x: x.get("published") or datetime(1970, 1, 1, tzinfo=timezone.utc),
        reverse=True,
    )


def fetch_query_results(query: str):
    url = build_rss_url(query)
    xml_text = fetch_url(url)
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item in channel.findall("item"):
        items.append(xml_item_to_dict(item))
    return items


@st.cache_data(ttl=240, show_spinner=False)
def fetch_news_for_disease(disease_name: str, config: dict, days_back: int, max_news_per_disease: int):
    raw_items = []
    queries = build_queries(config["queries"], days_back)
    match_terms = config["match_terms"]

    with ThreadPoolExecutor(max_workers=min(6, len(queries))) as executor:
        future_map = {executor.submit(fetch_query_results, q): q for q in queries}
        for future in as_completed(future_map):
            try:
                raw_items.extend(future.result())
            except Exception:
                pass

    filtered = []
    for item in raw_items:
        combined_text = " ".join(
            [
                item.get("title", ""),
                item.get("description", ""),
                item.get("source", ""),
            ]
        )

        if not is_recent(item.get("published"), days_back):
            continue
        if not contains_disease(combined_text, match_terms):
            continue
        if not contains_region(combined_text):
            continue

        item["disease"] = disease_name
        item["report_color"] = config.get("report_color", "#0b3b7a")
        filtered.append(item)

    filtered = deduplicate_news(filtered)
    filtered = sort_news(filtered)
    return filtered[:max_news_per_disease]


# =========================================================
# INFORME HTML
# =========================================================
def summarize_selected_news(selected_items):
    if not selected_items:
        return "No hay noticias seleccionadas."

    disease_counts = Counter(item["disease"] for item in selected_items)
    source_counts = Counter(item["source"] for item in selected_items)

    parts = []
    parts.append(
        f"Se han seleccionado {len(selected_items)} noticias correspondientes a {len(disease_counts)} epizootias y {len(source_counts)} fuentes distintas."
    )

    disease_fragments = [f"{disease}: {count}" for disease, count in disease_counts.items()]
    parts.append("Distribución por enfermedad: " + "; ".join(disease_fragments) + ".")

    top_sources = source_counts.most_common(5)
    if top_sources:
        source_fragments = [f"{source} ({count})" for source, count in top_sources]
        parts.append("Fuentes con mayor presencia: " + ", ".join(source_fragments) + ".")

    headline_snippets = []
    for item in selected_items[:6]:
        headline_snippets.append(item["title"])

    if headline_snippets:
        parts.append(
            "Titulares clave: " + " | ".join(headline_snippets) + "."
        )

    return " ".join(parts)


def summarize_sources(selected_items):
    if not selected_items:
        return []

    grouped = {}
    for item in selected_items:
        source = item["source"]
        grouped.setdefault(source, []).append(item)

    result = []
    for source, items in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        diseases = Counter(item["disease"] for item in items)
        disease_text = ", ".join([f"{k}: {v}" for k, v in diseases.items()])
        newest = max([i.get("published") for i in items if i.get("published")], default=None)
        result.append(
            {
                "source": source,
                "count": len(items),
                "diseases": disease_text,
                "latest": format_dt(newest) if newest else "Fecha no disponible",
            }
        )
    return result


def html_escape(text: str) -> str:
    return html.escape(text or "")


def report_banner_html():
    banner_uri = image_to_data_uri(PINK_BANNER_PATH)
    if not banner_uri:
        return ""
    return f'<div style="margin:0 0 18px 0;"><img src="{banner_uri}" style="width:100%;max-height:140px;object-fit:cover;border-radius:10px;"/></div>'


def report_logo_html(path: str, width: int):
    data_uri = image_to_data_uri(path)
    if not data_uri:
        return ""
    return f'<img src="{data_uri}" style="max-width:{width}px;height:auto;"/>'


def build_html_report(selected_items, days_back: int) -> str:
    now_txt = datetime.now().astimezone().strftime("%d/%m/%Y %H:%M:%S")
    executive_summary = summarize_selected_news(selected_items)
    source_summary = summarize_sources(selected_items)

    grouped = {}
    for item in selected_items:
        grouped.setdefault(item["disease"], []).append(item)

    disease_sections = []
    for disease, items in grouped.items():
        items = sort_news(items)
        color = items[0].get("report_color", "#0b3b7a") if items else "#0b3b7a"
        cards = []
        for item in items:
            desc = item.get("description") or "Sin resumen disponible."
            cards.append(
                f"""
                <div class="news-card">
                    <div class="news-meta"><strong>{html_escape(item.get('source',''))}</strong> · {html_escape(format_dt(item.get('published')))}</div>
                    <div class="news-title"><a href="{html_escape(item.get('link',''))}" target="_blank">{html_escape(item.get('title',''))}</a></div>
                    <div class="news-desc">{html_escape(desc)}</div>
                    <div class="news-link"><a href="{html_escape(item.get('link',''))}" target="_blank">Abrir noticia</a></div>
                </div>
                """
            )
        disease_sections.append(
            f"""
            <section class="disease-section">
                <div class="section-title" style="border-left:8px solid {color};">{html_escape(disease)}</div>
                {''.join(cards)}
            </section>
            """
        )

    source_rows = []
    for row in source_summary:
        source_rows.append(
            f"""
            <tr>
                <td>{html_escape(row['source'])}</td>
                <td>{row['count']}</td>
                <td>{html_escape(row['diseases'])}</td>
                <td>{html_escape(row['latest'])}</td>
            </tr>
            """
        )

    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Informe Noticias Epizootias</title>
<style>
    body {{
        margin: 0;
        font-family: Arial, Helvetica, sans-serif;
        color: #1e1e1e;
        background: #f4f6f8;
    }}
    .page {{
        max-width: 1180px;
        margin: 0 auto;
        background: #ffffff;
        padding: 22px 28px 40px 28px;
    }}
    .header-grid {{
        display: grid;
        grid-template-columns: 1.8fr 0.8fr;
        gap: 20px;
        align-items: center;
        margin-bottom: 10px;
    }}
    .title {{
        font-size: 34px;
        font-weight: 800;
        color: #0b3b7a;
        margin: 8px 0 4px 0;
    }}
    .subtitle {{
        font-size: 16px;
        color: #4f4f4f;
        margin-bottom: 4px;
    }}
    .meta {{
        font-size: 13px;
        color: #666666;
        margin-top: 8px;
    }}
    .box {{
        border: 1px solid #e0e0e0;
        border-radius: 14px;
        padding: 16px 18px;
        margin-top: 18px;
        background: #fbfbfc;
    }}
    .box h2 {{
        margin: 0 0 10px 0;
        font-size: 20px;
        color: #0b3b7a;
    }}
    .section-title {{
        font-size: 22px;
        font-weight: 800;
        color: #1f1f1f;
        padding: 8px 0 8px 14px;
        margin: 28px 0 14px 0;
        background: #fafafa;
        border-radius: 8px;
    }}
    .news-card {{
        border: 1px solid #e5e5e5;
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 14px;
        background: #ffffff;
    }}
    .news-meta {{
        font-size: 13px;
        color: #666666;
        margin-bottom: 6px;
    }}
    .news-title {{
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 8px;
        line-height: 1.35;
    }}
    .news-title a, .news-link a {{
        color: #0b3b7a;
        text-decoration: none;
    }}
    .news-desc {{
        font-size: 14px;
        color: #333333;
        line-height: 1.5;
        margin-bottom: 8px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }}
    th, td {{
        border: 1px solid #e2e2e2;
        padding: 10px 8px;
        text-align: left;
        vertical-align: top;
    }}
    th {{
        background: #f0f3f7;
        color: #0b3b7a;
    }}
</style>
</head>
<body>
    <div class="page">
        {report_banner_html()}
        <div class="header-grid">
            <div>
                {report_logo_html(NUTRECO_LOGO_PATH, 380)}
                <div class="title">Noticias Epizootias</div>
                <div class="subtitle">Informe HTML de noticias seleccionadas sobre DNC, IAAP, PPA y Enfermedad de Newcastle</div>
                <div class="meta">Generado el {html_escape(now_txt)} · Ventana de búsqueda: últimos {days_back} días · Nº de noticias seleccionadas: {len(selected_items)}</div>
            </div>
            <div style="text-align:right;">
                {report_logo_html(TECHTEAM_LOGO_PATH, 180)}
            </div>
        </div>

        <div class="box">
            <h2>Resumen ejecutivo</h2>
            <div>{html_escape(executive_summary)}</div>
        </div>

        <div class="box">
            <h2>Resumen de fuentes seleccionadas</h2>
            <table>
                <thead>
                    <tr>
                        <th>Fuente</th>
                        <th>Nº noticias</th>
                        <th>Distribución por enfermedad</th>
                        <th>Noticia más reciente</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(source_rows) if source_rows else '<tr><td colspan="4">Sin datos</td></tr>'}
                </tbody>
            </table>
        </div>

        {''.join(disease_sections)}
    </div>
</body>
</html>
"""


def html_to_download_bytes(report_html: str) -> bytes:
    buffer = BytesIO()
    buffer.write(report_html.encode("utf-8"))
    return buffer.getvalue()


# =========================================================
# RENDER NOTICIAS
# =========================================================
def render_news_card(item: dict, idx: int):
    title = item.get("title", "Sin título")
    link = item.get("link", "")
    source = item.get("source", "Medio no identificado")
    desc = item.get("description", "") or "Sin resumen disponible."
    if len(desc) > 360:
        desc = desc[:357] + "..."
    published = item.get("published")
    check_key = f"sel::{item['disease']}::{item.get('link','')}"

    st.markdown(
        f"""
        <div style="
            border: 1px solid rgba(128,128,128,0.25);
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.02);
        ">
            <div style="font-size: 0.9rem; opacity: 0.82; margin-bottom: 6px;">
                <strong>{idx}.</strong> {html_escape(source)} · {format_dt(published)} · {time_ago(published)}
            </div>
            <div style="font-size: 1.03rem; font-weight: 700; line-height: 1.35; margin-bottom: 8px; color: #0b3b7a;">
                <a href="{html_escape(link)}" target="_blank" style="text-decoration: none; color: inherit;">{html_escape(title)}</a>
            </div>
            <div style="font-size: 0.95rem; opacity: 0.94; margin-bottom: 8px;">
                {html_escape(desc)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.checkbox("Seleccionar para informe", key=check_key)


# =========================================================
# AUTOREFRESH
# =========================================================
def auto_refresh_fragment(func):
    if hasattr(st, "fragment"):
        return st.fragment(run_every=AUTO_REFRESH)(func)
    return func


# =========================================================
# APP UI
# =========================================================
st.set_page_config(page_title=APP_TITLE, layout="wide")

inject_brand_css()
render_brand_header()

with st.sidebar:
    st.header("Filtros")
    days_back = st.number_input(
        "Buscar noticias publicadas en los últimos días",
        min_value=MIN_DAYS_BACK,
        max_value=MAX_DAYS_BACK,
        value=DEFAULT_DAYS_BACK,
        step=1,
    )
    max_news_per_disease = st.number_input(
        "Máximo de noticias por enfermedad",
        min_value=3,
        max_value=15,
        value=DEFAULT_MAX_NEWS_PER_DISEASE,
        step=1,
    )
    st.caption("La app se reconsulta automáticamente cada 5 minutos.")
    st.caption("Puedes seleccionar noticias y generar un informe HTML corporativo.")

col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    st.metric("Enfermedades monitorizadas", len(DISEASES))
with col_b:
    st.metric("Noticias por enfermedad", max_news_per_disease)
with col_c:
    st.metric("Ventana temporal", f"Últimos {days_back} días")

controls_col1, controls_col2 = st.columns([1, 1])
with controls_col1:
    if st.button("Actualizar ahora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with controls_col2:
    if st.button("Deseleccionar todas las noticias", use_container_width=True):
        for key in list(st.session_state.keys()):
            if str(key).startswith("sel::"):
                st.session_state[key] = False
        st.rerun()


@auto_refresh_fragment
def render_monitor():
    st.caption(
        f"Última actualización de la vista: {datetime.now().astimezone().strftime('%d/%m/%Y %H:%M:%S')}"
    )

    with st.spinner("Buscando noticias frescas..."):
        results = {}
        for disease_name, config in DISEASES.items():
            results[disease_name] = fetch_news_for_disease(
                disease_name,
                config,
                int(days_back),
                int(max_news_per_disease),
            )

    total_found = sum(len(v) for v in results.values())
    st.success(f"Noticias encontradas en esta actualización: {total_found}")

    all_items = []
    tabs = st.tabs(list(DISEASES.keys()))

    for tab, disease_name in zip(tabs, DISEASES.keys()):
        items = results[disease_name]
        all_items.extend(items)

        with tab:
            if not items:
                st.warning("No se han encontrado noticias que cumplan los filtros en este momento.")
            else:
                for idx, item in enumerate(items, start=1):
                    render_news_card(item, idx)

    selected_items = []
    for item in all_items:
        check_key = f"sel::{item['disease']}::{item.get('link','')}"
        if st.session_state.get(check_key, False):
            selected_items.append(item)

    st.markdown("---")
    st.subheader("Informe HTML")
    st.markdown('<div class="report-preview">', unsafe_allow_html=True)
    st.write(f"Noticias seleccionadas: **{len(selected_items)}**")

    if selected_items:
        st.write("**Resumen automático:**")
        st.write(summarize_selected_news(selected_items))

        st.write("**Fuentes seleccionadas:**")
        for row in summarize_sources(selected_items):
            st.write(f"- {row['source']}: {row['count']} noticias · {row['diseases']} · última: {row['latest']}")

        report_html = build_html_report(selected_items, int(days_back))
        st.download_button(
            "Descargar informe HTML",
            data=html_to_download_bytes(report_html),
            file_name="informe_noticias_epizootias.html",
            mime="text/html",
            use_container_width=True,
        )
    else:
        st.info("Selecciona noticias en las pestañas superiores para generar el informe HTML.")

    st.markdown("</div>", unsafe_allow_html=True)


render_monitor()
