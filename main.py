import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración de la App
st.set_page_config(page_title="Monitor Sanidad Animal", layout="wide")

st.title("🛰️ Monitor Sanidad Animal")
st.write(f"✅ Consulta automática realizada a las: **{datetime.now().strftime('%H:%M:%S')}**")

# 2. FUENTES SELECCIONADAS
FUENTES = [
    {"n": "MAPA (Ministerio)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/"},
    {"n": "Eurocarne", "u": "https://www.eurocarne.com/rss"},
    {"n": "3Tres3 (Sector Porcino)", "u": "https://www.3tres3.com/rss/noticias"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/"}
]

# 3. DICCIONARIOS DE BÚSQUEDA (Más amplios para asegurar contenido)
PALABRAS_VACUNO = ["nodular", "dermatosis", "vaca", "vacuno", "bovino", "lengua azul", "ganado", "leche", "ternera"]
PALABRAS_AVES = ["aviar", "iaap", "gripe", "ave", "pollo", "gallina", "avícola", "huevo"]
PALABRAS_PORCINO = ["peste", "ppa", "asf", "cerdo", "porcino", "jabali", "lechon", "cárnico", "embutido"]

def cargar_rss(url):
    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]
        with opener.open(url, timeout=20) as response:
            return feedparser.parse(response.read())
    except: return None

def obtener_todas_las_noticias():
    noticias = []
    for f in FUENTES:
        feed = cargar_rss(f['u'])
        if feed and feed.entries:
            for e in feed.entries:
                texto = (e.get('title', '') + " " + e.get('summary', '')).lower()
                
                # Clasificación
                cat = "General"
                if any(k in texto for k in PALABRAS_VACUNO): cat = "🐄 VACUNO"
                elif any(k in texto for k in PALABRAS_AVES): cat = "🦆 AVES"
                elif any(k in texto for k in PALABRAS_PORCINO): cat = "🐖 PORCINO"
                
                noticias.append({
                    "t": e.get('title', 'Sin título'),
                    "l": e.get('link', '#'),
                    "f": f['n'],
                    "c": cat
                })
    return noticias

# --- PROCESAMIENTO ---
todas_noticias = obtener_todas_las_noticias()

# Creamos las columnas
col1, col2, col3 = st.columns(3)
secciones = [
    {"titulo": "🐄 VACUNO", "col": col1, "filtro": "🐄 VACUNO"},
    {"titulo": "🦆 AVES", "col": col2, "filtro": "🦆 AVES"},
    {"titulo": "🐖 PORCINO", "col": col3, "filtro": "🐖 PORCINO"}
]

for s in secciones:
    with s['col']:
        st.header(s['titulo'])
        
        # 1. Buscamos noticias específicas
        especificas = [n for n in todas_noticias if n['c'] == s['filtro']]
        
        # Eliminamos duplicados
        vistos = set()
        filtradas = [n for n in especificas if n['t'] not in vistos and not vistos.add(n['t'])]
        
        if filtradas:
            for n in filtradas[:15]:
                with st.container():
                    st.info(f"**{n['t']}**\n\n📍 Fuente: {n['f']}")
                    st.link_button("👉 VER NOTICIA", n['l'])
                    st.divider()
        else:
            # 2. Si no hay específicas, mostramos las últimas generales de los medios de ese sector
            st.write("📢 *Sin alertas críticas hoy. Últimas noticias del sector:*")
            # Para vacuno y porcino, Eurocarne y Agrodigital siempre tienen algo
            generales = [n for n in todas_noticias if n['f'] in ["Eurocarne", "Agrodigital", "3Tres3 (Sector Porcino)"]]
            for n in generales[:5]:
                st.caption(f"**{n['t']}** ({n['f']})")
                st.link_button("Leer más", n['l'], key=n['l']+s['titulo'])
                st.write("")

# Botón manual al final
if st.button('🔄 ACTUALIZAR AHORA'):
    st.rerun()
