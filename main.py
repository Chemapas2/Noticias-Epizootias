import csv
import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from io import StringIO

import streamlit as st


# =========================
# Configuración general
# =========================
APP_TITLE = "Noticias Epizootias"
AUTO_REFRESH = "5m"
MAX_NEWS_PER_DISEASE = 5
DAYS_BACK = 7
TIMEOUT_SECONDS = 20

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
            '"dermatitis nodular contagiosa" (vacuno OR bovino) (España OR Portugal OR Europa OR UE OR "Unión Europea") when:7d',
            '"lumpy skin disease" (vacuno OR bovino) (España OR Portugal OR Europa OR UE OR "Unión Europea") when:7d',
            'DNC vacuno (España OR Portugal OR Europa OR UE) when:7d',
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
            '("influenza aviar" OR "gripe aviar" OR IAAP OR HPAI) (aves OR aviar OR poultry) (España OR Portugal OR Europa OR UE OR "Unión Europea") when:7d',
            '"influenza aviar altamente patógena" (España OR Portugal OR Europa OR UE) when:7d',
            '"gripe aviar" (España OR Portugal OR Europa OR UE) when:7d',
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
            '("peste porcina africana" OR PPA OR ASF) (porcino OR cerdo OR cerdos OR jabalí OR jabalies OR jabalíes) (España OR Portugal OR Europa OR UE OR "Unión Europea") when:7d',
            '"peste porcina africana" (España OR Portugal OR Europa OR UE) when:7d',
            'PPA porcino (España OR Portugal OR Europa OR UE) when:7d',
        ],
        "match_terms": [
            "peste porcina africana",
            "ppa",
            "asf",
        ],
    },
}


# =========================
# Utilidades
# =========================
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


def contains_disease(text: str, disease_terms: list[str]) -> bool:
    t = text_to_key(text)
    return any(term in t for term in disease_terms)


def is_recent(dt: datetime, days_back: int = DAYS_BACK) -> bool:
    if not dt:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    return dt >= cutoff


def deduplicate_news(items: list[dict]) -> list[dict]:
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


def sort_news(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda x: x.get("published") or datetime(1970, 1, 1, tzinfo=timezone.utc),
        reverse=True,
    )


def fetch_query_results(query: str) -> list[dict]:
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
def fetch_news_for_disease(disease_name: str, config: dict) -> list[dict]:
    raw_items = []
    queries = config["queries"]
    match_terms = config["match_terms"]

    with ThreadPoolExecutor(max_workers=min(6, len(queries))) as executor:
        future_map = {executor.submit(fetch_query_results, q): q for q in queries}
        for future in as_completed(future_map):
            try:
                raw_items.extend(future.result())
            except Exception:
                # Silencioso: la app sigue con el resto de consultas
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

        if not is_recent(item.get("published")):
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


def build_csv_bytes(all_items: list[dict]) -> bytes:
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


def render_news_card(item: dict, idx: int):
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
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 12px;
            background: rgba(255,255,255,0.02);
        ">
            <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 6px;">
                <strong>{idx}.</strong> {source} · {format_dt(published)} · {time_ago(published)}
            </div>
            <div style="font-size: 1.02rem; font-weight: 700; line-height: 1.35; margin-bottom: 8px;">
                <a href="{link}" target="_blank" style="text-decoration: none; color: inherit;">{html.escape(title)}</a>
            </div>
            <div style="font-size: 0.95rem; opacity: 0.92;">
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


# =========================
# UI
# =========================
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.caption(
    "Monitor automático de DNC, IAAP y PPA en medios en español, enfocado en noticias sobre España, Portugal y Europa de los últimos 7 días."
)

col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    st.metric("Enfermedades monitorizadas", len(DISEASES))
with col_b:
    st.metric("Noticias por enfermedad", MAX_NEWS_PER_DISEASE)
with col_c:
    st.metric("Ventana temporal", f"Últimos {DAYS_BACK} días")

if st.button("Actualizar ahora", use_container_width=True):
    st.cache_data.clear()
    st.rerun()


@auto_refresh_fragment
def render_monitor():
    st.caption(f"Última actualización de la vista: {datetime.now().astimezone().strftime('%d/%m/%Y %H:%M:%S')}")

    with st.spinner("Buscando noticias..."):
        results = {}
        for disease_name, config in DISEASES.items():
            results[disease_name] = fetch_news_for_disease(disease_name, config)

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
