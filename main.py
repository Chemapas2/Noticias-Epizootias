import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración de la App
st.set_page_config(page_title="Monitor Sanidad Animal", layout="wide")

st.title("🛰️ Monitor Sanidad Animal (PPA / DNC / IAAP)")
st.write(f"✅ Última conexión oficial: **{datetime.now().strftime('%H:%M:%S')}**")

# 2. FUENTES (Re-verificadas)
FUENTES = [
    {"n": "MAPA (Ministerio)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/"},
    {"n": "Eurocarne", "u": "https://www.eurocarne.com/rss"},
    {"n": "3Tres3 (Cerdo)", "u": "https://www.3tres3.com/rss/noticias"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/"}
]

# 3. FILTROS AGRESIVOS
# He añadido términos que usan las agencias de noticias para que no falle
PALABRAS_VACUNO = ["nodular", "dermatosis", "vaca", "vacuno", "bovino", "lengua azul", "ganado", "rumiante", "epizootia"]
PALABRAS_AVES = ["aviar", "iaap", "gripe", "ave", "pollo", "gallina", "h5n1", "avícola"]
PALABRAS_PORCINO = ["peste", "ppa", "asf", "cerdo", "porcino", "jabali", "lechon", "africana", "foco"]

def cargar_rss(url):
    try:
        # Simulamos un navegador muy común para evitar bloqueos del Ministerio
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')]
        with opener.open(url, timeout=20) as response:
            return feedparser.parse(response.read())
    except:
        return None

def obtener_alertas():
    noticias = []
    for f in FUENTES:
        feed = cargar_rss(f['u'])
        if feed and feed.entries:
            for e in feed.entries:
                # Unimos título y descripción para buscar mejor
                contenido = (e.get('title', '') + " " + e.get('description', '') + " " + e.get('summary', '')).lower()
                
                cat = None
                if any(k in contenido for k in PALABRAS_VACUNO): cat = "🐄 VACUNO"
                elif any(k in contenido for k in PALABRAS_AVES): cat = "🦆 AVES"
                elif any(k in contenido for k in PALABRAS_PORCINO): cat = "🐖 PORCINO"
                
                if cat:
                    noticias.append({
                        "t": e.title,
                        "l": e.link,
                        "f": f['n'],
                        "c": cat
                    })
    return noticias

# --- MOSTRAR DATOS ---
items = obtener_alertas()

# Botón de refresco manual
if st.button('🔄 REFRESCAR NOTICIAS AHORA'):
    st.rerun()

col1, col2, col3 = st.columns(3)
secciones = [("🐄 VACUNO", col1), ("🦆 AVES", col2), ("🐖 PORCINO", col3)]

for nombre_cat, columna in secciones:
    with columna:
        st.header(nombre_cat)
        # Filtro único para no repetir noticias de distintas fuentes
        titulos_vistos = set()
        filtradas = [n for n in items if n['c'] == nombre_cat and n['t'] not in titulos_vistos and not titulos_vistos.add(n['t'])]
        
        if filtradas:
            for n in filtradas[:15]:
                with st.container():
                    st.info(f"**{n['t']}**\n\n📍 Fuente: {n['f']}")
                    st.link_button("👉 LEER NOTICIA", n['l'])
                    st.divider()
        else:
            st.write("No se han encontrado alertas críticas hoy.")
