import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración de la App
st.set_page_config(page_title="Monitor Sanidad Animal", layout="wide")

st.title("🛰️ Monitor Sanidad Animal")
st.write(f"✅ Estado: Conectado a fuentes oficiales | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# 2. FUENTES (Aumentamos fuentes para asegurar volumen de noticias)
FUENTES = [
    {"n": "MAPA (Ministerio)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/"},
    {"n": "Eurocarne", "u": "https://www.eurocarne.com/rss"},
    {"n": "3Tres3 (Porcino)", "u": "https://www.3tres3.com/rss/noticias"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/"},
    {"n": "Agropopular", "u": "https://www.agropopular.com/feed/"},
    {"n": "Interempresas Ganadería", "u": "https://www.interempresas.net/RSS/RssFicha.asp?IdF=64"}
]

# 3. FILTROS DE MEMORIA (Palabras muy amplias para capturar TODO)
P_VACUNO = ["nodular", "dermatosis", "vaca", "vacuno", "bovino", "lengua azul", "ganado", "leche", "rumiante", "explotación", "ehp"]
P_AVES = ["aviar", "iaap", "gripe", "ave", "pollo", "gallina", "h5n1", "avícola", "huevo", "granja"]
P_PORCINO = ["peste", "ppa", "asf", "cerdo", "porcino", "jabali", "lechon", "cárnico", "sector porcino", "matadero"]

def cargar_rss(url):
    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')]
        with opener.open(url, timeout=20) as resp:
            return feedparser.parse(resp.read())
    except: return None

# Usamos caché para que las noticias se "peguen" a la app y no desaparezcan
@st.cache_data(ttl=3600)
def obtener_historial():
    archivo_noticias = []
    for f in FUENTES:
        feed = cargar_rss(f['u'])
        if feed and feed.entries:
            for e in feed.entries:
                texto = (e.get('title', '') + " " + e.get('summary', '') + " " + e.get('description', '')).lower()
                
                # Clasificar
                categoria = None
                if any(k in texto for k in P_VACUNO): categoria = "🐄 VACUNO"
                elif any(k in texto for k in P_AVES): categoria = "🦆 AVES"
                elif any(k in texto for k in P_PORCINO): categoria = "🐖 PORCINO"
                
                if categoria:
                    archivo_noticias.append({
                        "t": e.title,
                        "l": e.link,
                        "f": f['n'],
                        "c": categoria
                    })
    return archivo_noticias

# --- PROCESAMIENTO ---
items = obtener_historial()

col1, col2, col3 = st.columns(3)
secciones = [("🐄 VACUNO", col1), ("🦆 AVES", col2), ("🐖 PORCINO", col3)]

for nombre_cat, col in secciones:
    with col:
        st.header(nombre_cat)
        
        # Filtrar por categoría y eliminar duplicados
        vistos = set()
        filtradas = [n for n in items if n['c'] == nombre_cat and n['t'] not in vistos and not vistos.add(n['t'])]
        
        if filtradas:
            for n in filtradas[:20]: # Mostramos hasta 20 para tener historial
                with st.container():
                    st.info(f"**{n['t']}**\n\n📍 Fuente: {n['f']}")
                    st.link_button("👉 LEER NOTICIA COMPLETA", n['l'])
                    st.divider()
        else:
            # Si el filtro falla, buscamos cualquier noticia del sector para no dejarlo vacío
            st.warning("⚠️ No hay alertas críticas hoy. Revisa el histórico oficial arriba.")

if st.button('🔄 REFRESCAR Y BUSCAR NUEVOS FOCOS'):
    st.cache_data.clear()
    st.rerun()
