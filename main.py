import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración de la App
st.set_page_config(page_title="Monitor Sanidad Animal", layout="wide")

st.title("🛰️ Monitor Sanidad Animal")
st.write(f"✅ Sistema Activo | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# 2. FUENTES ORGANIZADAS
FUENTES = [
    {"n": "3Tres3 (Cerdos)", "u": "https://www.3tres3.com/rss/noticias", "cat": "🐖 PORCINO"},
    {"n": "Avicultura", "u": "https://www.avicultura.com/feed/", "cat": "🦆 AVES"},
    {"n": "Eurocarne", "u": "https://www.eurocarne.com/rss", "cat": "MIXTO"},
    {"n": "MAPA (Ministerio)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx", "cat": "MIXTO"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/", "cat": "MIXTO"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/", "cat": "MIXTO"}
]

# Palabras clave para identificación
P_VACUNO = ["vaca", "vacuno", "bovino", "nodular", "dermatosis", "lengua azul", "leche", "ternera"]
P_AVES = ["aviar", "gripe", "ave", "pollo", "gallina", "huevo", "iaap", "avicultura"]
P_PORCINO = ["cerdo", "porcino", "peste", "ppa", "jamon", "lechon", "matadero", "porcina"]

def cargar_rss(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return feedparser.parse(resp.read())
    except: return None

def obtener_noticias():
    todas = []
    for f in FUENTES:
        feed = cargar_rss(f['u'])
        if feed and feed.entries:
            for e in feed.entries:
                titulo = e.get('title', '')
                resumen = e.get('summary', e.get('description', '')).lower()
                link = e.get('link', '#')
                texto_total = (titulo + " " + resumen).lower()
                
                # Clasificar por contenido
                cat_detectada = None
                if any(k in texto_total for k in P_PORCINO) or f['cat'] == "🐖 PORCINO": cat_detectada = "🐖 PORCINO"
                elif any(k in texto_total for k in P_VACUNO): cat_detectada = "🐄 VACUNO"
                elif any(k in texto_total for k in P_AVES) or f['cat'] == "🦆 AVES": cat_detectada = "🦆 AVES"
                
                if cat_detectada:
                    todas.append({"t": titulo, "l": link, "f": f['n'], "c": cat_detectada})
                elif f['cat'] == "MIXTO":
                    # Guardar como general por si falta relleno
                    todas.append({"t": titulo, "l": link, "f": f['n'], "c": "GENERAL"})
    return todas

# --- LÓGICA DE MOSTRAR ---
noticias = obtener_noticias()
col1, col2, col3 = st.columns(3)

secciones = [
    ("🐄 VACUNO", col1, P_VACUNO),
    ("🦆 AVES", col2, P_AVES),
    ("🐖 PORCINO", col3, P_PORCINO)
]

for nombre_cat, columna, keywords in secciones:
    with columna:
        st.header(nombre_cat)
        
        # 1. Noticias específicas del sector
        especificas = []
        vistos = set()
        for n in noticias:
            if n['c'] == nombre_cat and n['t'] not in vistos:
                especificas.append(n)
                vistos.add(n['t'])
        
        # 2. Si no hay 5, rellenamos con noticias generales de fuentes de confianza
        if len(especificas) < 5:
            generales = [n for n in noticias if n['c'] == "GENERAL" and n['t'] not in vistos]
            especificas.extend(generales[:(5 - len(especificas))])
        
        # Mostrar resultados (mínimo 5 si existen en el sistema)
        for n in especificas[:8]:
            with st.container():
                st.info(f"**{n['t']}**\n\n📍 {n['f']}")
                st.link_button("👉 LEER NOTICIA", n['l'])
                st.divider()

if st.button('🔄 ACTUALIZAR AHORA'):
    st.rerun()
