import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración de la App
st.set_page_config(page_title="Monitor Sanidad Animal", layout="wide")

st.title("🛰️ Monitor Sanidad Animal")
st.write(f"✅ Filtros optimizados | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# 2. FUENTES CON PRIORIDADES
FUENTES = [
    {"n": "3Tres3 (Especializado Porcino)", "u": "https://www.3tres3.com/rss/noticias", "sector": "🐖 PORCINO"},
    {"n": "Eurocarne (Cárnico)", "u": "https://www.eurocarne.com/rss", "sector": "🐖 PORCINO"},
    {"n": "Ministerio (MAPA)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx", "sector": "MIXTO"},
    {"n": "Avicultura", "u": "https://www.avicultura.com/feed/", "sector": "🦆 AVES"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/", "sector": "MIXTO"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/", "sector": "MIXTO"}
]

P_VACUNO = ["vaca", "vacuno", "bovino", "nodular", "dermatosis", "lengua azul", "ganado", "leche"]
P_AVES = ["aviar", "gripe", "ave", "pollo", "gallina", "huevo", "iaap"]
P_PORCINO = ["cerdo", "porcino", "peste", "ppa", "asf", "lechon", "ibérico", "cárnico", "matadero", "porcina"]

def cargar_rss(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return feedparser.parse(resp.read())
    except: return None

def obtener_noticias_garantizadas():
    # Estructura para almacenar por categoría
    almacen = {"🐄 VACUNO": [], "🦆 AVES": [], "🐖 PORCINO": []}
    vistos = set()

    for f in FUENTES:
        feed = cargar_rss(f['u'])
        if feed and feed.entries:
            for e in feed.entries:
                titulo = e.get('title', '')
                if titulo in vistos: continue
                
                resumen = (e.get('summary', '') + " " + e.get('description', '')).lower()
                texto = (titulo + " " + resumen).lower()
                link = e.get('link', '#')
                item = {"t": titulo, "l": link, "f": f['n']}

                # CLASIFICACIÓN AGRESIVA
                # Porcino: si la fuente es especializada o tiene keywords
                if f['sector'] == "🐖 PORCINO" or any(k in texto for k in P_PORCINO):
                    almacen["🐖 PORCINO"].append(item)
                    vistos.add(titulo)
                # Aves: si la fuente es especializada o tiene keywords
                elif f['sector'] == "🦆 AVES" or any(k in texto for k in P_AVES):
                    almacen["🦆 AVES"].append(item)
                    vistos.add(titulo)
                # Vacuno
                elif any(k in texto for k in P_VACUNO):
                    almacen["🐄 VACUNO"].append(item)
                    vistos.add(titulo)
                # Si no encaja en ninguna pero es del Ministerio o Agrodigital, guardamos para relleno
                elif f['sector'] == "MIXTO":
                    # Lo guardamos temporalmente por si alguna columna queda con menos de 5
                    if len(almacen["🐄 VACUNO"]) < 5: almacen["🐄 VACUNO"].append(item)
                    elif len(almacen["🦆 AVES"]) < 5: almacen["🦆 AVES"].append(item)
                    elif len(almacen["🐖 PORCINO"]) < 5: almacen["🐖 PORCINO"].append(item)
                    vistos.add(titulo)

    return almacen

# --- INTERFAZ ---
dict_noticias = obtener_noticias_garantizadas()
col1, col2, col3 = st.columns(3)

secciones = [
    ("🐄 VACUNO", col1),
    ("🦆 AVES", col2),
    ("🐖 PORCINO", col3)
]

for nombre_cat, columna in secciones:
    with columna:
        st.header(nombre_cat)
        lista = dict_noticias[nombre_cat]
        
        # Mostramos mínimo 5, máximo 10
        for n in lista[:10]:
            with st.container():
                st.info(f"**{n['t']}**\n\n📍 Fuente: {n['f']}")
                st.link_button("👉 LEER NOTICIA", n['l'], key=n['l']+nombre_cat)
                st.divider()

if st.button('🔄 ACTUALIZAR MONITOR'):
    st.rerun()
