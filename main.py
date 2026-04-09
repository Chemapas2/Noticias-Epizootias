import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

st.set_page_config(page_title="Monitor Sanidad Animal", layout="wide")

st.title("🛰️ Monitor Sanidad Animal")
st.write(f"✅ Conectado | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# FUENTES (Re-ordenadas por eficacia en Porcino)
FUENTES = [
    {"n": "3Tres3 (Líder Porcino)", "u": "https://www.3tres3.com/rss/noticias"},
    {"n": "Eurocarne (Cárnico)", "u": "https://www.eurocarne.com/rss"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/"},
    {"n": "MAPA (Ministerio)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/"}
]

# PALABRAS CLAVE (Aumentadas para capturar TODO el sector)
P_VACUNO = ["nodular", "dermatosis", "vaca", "vacuno", "bovino", "lengua azul", "ganado", "ehp"]
P_AVES = ["aviar", "iaap", "gripe", "ave", "pollo", "gallina", "h5n1"]
P_PORCINO = ["peste", "ppa", "asf", "cerdo", "porcino", "jabali", "lechon", "cárnico", "ibérico", "matadero", "porcina"]

def cargar_rss(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return feedparser.parse(resp.read())
    except: return None

def obtener_noticias():
    noticias = []
    for f in FUENTES:
        feed = cargar_rss(f['u'])
        if feed and feed.entries:
            for e in feed.entries:
                # Buscamos en todo el texto disponible
                titulo = e.get('title', '')
                resumen = e.get('summary', e.get('description', ''))
                link = e.get('link', '')
                todo_texto = (titulo + " " + resumen + " " + link).lower()
                
                cat = None
                # Si la URL contiene 'porcino' o 'cerdo', va directo a esa categoría
                if "porcino" in todo_texto or "cerdo" in todo_texto or any(k in todo_texto for k in P_PORCINO):
                    cat = "🐖 PORCINO"
                elif any(k in todo_texto for k in P_VACUNO):
                    cat = "🐄 VACUNO"
                elif any(k in todo_texto for k in P_AVES):
                    cat = "🦆 AVES"
                
                if cat:
                    noticias.append({"t": titulo, "l": link, "f": f['n'], "c": cat})
    return noticias

# --- MOSTRAR ---
items = obtener_noticias()

col1, col2, col3 = st.columns(3)
secciones = [("🐄 VACUNO", col1), ("🦆 AVES", col2), ("🐖 PORCINO", col3)]

for nombre_cat, col in secciones:
    with col:
        st.header(nombre_cat)
        vistos = set()
        # Filtramos y quitamos repetidos
        filtradas = [n for n in items if n['c'] == nombre_cat and n['t'] not in vistos and not vistos.add(n['t'])]
        
        if filtradas:
            for n in filtradas[:15]:
                with st.container():
                    st.info(f"**{n['t']}**\n\n📍 Fuente: {n['f']}")
                    st.link_button("👉 LEER NOTICIA", n['l'])
                    st.divider()
        else:
            st.warning(f"No hay noticias recientes de {nombre_cat.lower()} en los boletines.")

if st.button('🔄 REFRESCAR NOTICIAS'):
    st.rerun()
