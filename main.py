import base64
import csv
import html
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from io import StringIO

import streamlit as st


# =========================================================
# CONFIGURACIÓN
# =========================================================
APP_TITLE = "Noticias Epizootias"
AUTO_REFRESH = "5m"
MAX_NEWS_PER_DISEASE = 5
DEFAULT_DAYS_BACK = 7
MIN_DAYS_BACK = 1
MAX_DAYS_BACK = 60
TIMEOUT_SECONDS = 20

# Archivos de imagen esperados en la misma carpeta que main.py
NUTRECO_LOGO_PATH = "Logo Nutreco.jpg"
TECHTEAM_LOGO_PATH = "Logo TechTeam 2.jpg"
PINK_BANNER_PATH = "Solapa rosa.jpg"

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=es&gl=ES&ceid=ES:es"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NoticiasEpizootias/1.0; +https://github.com/)"
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
    },
}


# =========================================================
# UTILIDADES DE MARCA
# =========================================================
def guess_mime_type(path):
    ext = os.path.splitext(path.lower())[1]
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    return "image/jpeg"


@st.cache_data(show_spinner=False)
def image_to_data_uri(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{guess_mime_type(path)};base64,{encoded}"


def inject_brand_css():
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.2rem;
                padding-bottom: 2rem;
            }

            .brand-title {
                font-size: 2.15rem;
                font-weight: 800;
                color: #0b3b7a;
                margin-top: 0.35rem;
                margin-bottom: 0.15rem;
            }

            .brand-subtitle {
                font-size: 0.98rem;
                color: #444444;
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
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_header():
    banner_uri = image_to_data_uri(PINK_BANNER_PATH)
    if banner_uri:
        st.markdown(
            f"""
            <div style="margin-bottom: 0.4rem;">
                <img src="{banner_uri}" style="width: 100%; border-radius: 10px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns([3.5, 1.3])

    with col1:
        if os.path.exists(NUTRECO_LOGO_PATH):
            st.image(NUTRECO_LOGO_PATH, use_container_width=True)

    with col2:
        if os.path.exists(TECHTEAM_LOGO_PATH):
            st.image(TECHTEAM_LOGO_PATH, width=190)

    st.markdown(f'<div class="brand-title">{APP_TITLE}</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="brand-subtitle">
            Monitor automático de DNC, IAAP y PPA en medios en español, con foco en España, Portugal y Europa.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# UTILIDADES DE DATOS
# =========================================================
def normalize_text(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def text_to_key(text):
    text = normalize_text(text).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_date(date_str):
    if not date_str:
        return None
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def format_dt(dt):
    if not dt:
        return "Fecha no disponible"
    return dt.astimezone().strftime("%d/%m/%Y %H:%M")


def time_ago(dt):
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


def build_rss_url(query):
    return GOOGLE_NEWS_RSS.format(query=urllib.parse.quote(query, safe=""))


def build_queries(base_queries, days_back):
    return [f"{q} when:{days_back}d" for q in base_queries]


def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", errors="ignore")


def xml_item_to_dict(item):
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


def contains_region(text):
    t = text_to_key(text)
    return any(term in t for term in REGION_TERMS)


def contains_disease(text, disease_terms):
    t = text_to_key(text)
    return any(term in t for term in disease_terms)


def is_recent(dt, days_back):
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


def fetch_query_results(query):
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
def fetch_news_for_disease(disease_name, config, days_back):
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

        filtered.append(item)

    filtered = deduplicate_news(filtered)
    filtered = sort_news(filtered)

    for item in filtered:
        item["disease"] = disease_name

    return filtered[:MAX_NEWS_PER_DISEASE]


def build_csv_bytes(all_items):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["enfermedad", "fecha", "medio", "titular", "resumen", "url"])

    for item in all_items:
        writer.writerow(
            [
                item.get("disease", ""),
                format_dt(item.get("published")),
                item.get("source", ""),
                item.get("title", ""),
                item.get("description", ""),
                item.get("link", ""),
            ]
        )

    return output.getvalue().encode("utf-8-sig")


def render_news_card(item, idx):
    title = item.get("title", "Sin título")
    link = item.get("link", "")
    source = item.get("source", "Medio no identificado")
    desc = item.get("description", "")
    if len(desc) > 320:
        desc = desc[:317] + "..."
    published = item.get("published")

    st.markdown(
        f"""
        <div style="
            border: 1px solid rgba(128,128,128,0.25);
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 12px;
            background: rgba(255,255,255,0.02);
        ">
            <div style="font-size: 0.9rem; opacity: 0.82; margin-bottom: 6px;">
                <strong>{idx}.</strong> {source} · {format_dt(published)} · {time_ago(published)}
            </div>
            <div style="font-size: 1.03rem; font-weight: 700; line-height: 1.35; margin-bottom: 8px; color: #0b3b7a;">
                <a href="{link}" target="_blank" style="text-decoration: none; color: inherit;">{html.escape(title)}</a>
            </div>
            <div style="font-size: 0.95rem; opacity: 0.94;">
                {html.escape(desc) if desc else "Sin resumen disponible."}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def auto_refresh_fragment(func):
    if hasattr(st, "fragment"):
        return st.fragment(run_every=AUTO_REFRESH)(func)
    return func


# =========================================================
# UI
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
    st.caption("La app se vuelve a consultar automáticamente cada 5 minutos.")
    st.caption("También puedes forzar una actualización manual con el botón principal.")

col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    st.metric("Enfermedades monitorizadas", len(DISEASES))
with col_b:
    st.metric("Noticias por enfermedad", MAX_NEWS_PER_DISEASE)
with col_c:
    st.metric("Ventana temporal", f"Últimos {days_back} días")

if st.button("Actualizar ahora", use_container_width=True):
    st.cache_data.clear()
    st.rerun()


@auto_refresh_fragment
def render_monitor():
    st.caption(
        f"Última actualización de la vista: {datetime.now().astimezone().strftime('%d/%m/%Y %H:%M:%S')}"
    )

    with st.spinner("Buscando noticias..."):
        results = {}
        for disease_name, config in DISEASES.items():
            results[disease_name] = fetch_news_for_disease(disease_name, config, days_back)

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

    if all_items:
        csv_bytes = build_csv_bytes(sort_news(all_items))
        st.download_button(
            "Descargar CSV",
            data=csv_bytes,
            file_name="noticias_epizootias.csv",
            mime="text/csv",
            use_container_width=True,
        )


render_monitor()
