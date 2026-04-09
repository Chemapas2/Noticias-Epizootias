import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración de la App
st.set_page_config(page_title="Monitor Epizootias v4", layout="wide")

# Título y hora de carga automática
st.title("🛰️ Monitor de Sanidad Animal")
st.write(f"✅ App actualizada automáticamente al abrir: **{datetime.now().strftime('%H:%M:%S')}**")

# 2. FUENTES OFICIALES
FUENTES = [
    {"n": "MAPA (Ministerio)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/"},
    {"n": "Eurocarne", "u": "https://www.eurocarne.com/rss"},
    {"n": "3Tres3 (Porcino)", "u": "https://www.3tres3.com/rss/noticias"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/"},
    {"n": "Agropopular", "u": "https://www.agropopular.com/feed/"}
]

# PALABRAS CLAVE AMPLIADAS (Filtro por sectores)
PALABRAS_VACUNO = ["nodular", "dermatosis", "vaca", "vacuno", "bovino", "lengua azul", "ganado", "rumiante", "explotación"]
PALABRAS_AVES = ["aviar", "iaap", "gripe", "ave", "pollo", "gallina", "h5n1", "explotación avícola"]
PALABRAS_PORCINO = ["peste", "ppa", "asf", "cerdo", "porcino", "jabali", "lechon", "cárnico", "matadero"]

# Función para evitar bloqueos
def cargar_datos_seguro(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return feedparser.parse(response.read())
    except:
        return None

# Eliminamos st.cache_data para que se refresque SOLA al entrar
def buscar_noticias():
    noticias = []
    for f in FUENTES:
        d = cargar_datos_seguro(f['u'])
        if d and d.entries:
            for e in d.entries:
                # Buscamos en título y resumen
                texto_busqueda = (e.get('title', '') + " " + e.get('summary', '')).lower()
                
                cat = None
                if any(k in texto_busqueda for k in PALABRAS_VACUNO): cat = "🐄 VACUNO"
                elif any(k in texto_busqueda for k in PALABRAS_AVES): cat = "🦆 AVES"
                elif any(k in texto_busqueda for k in PALABRAS_PORCINO): cat = "🐖 PORCINO"
                
                if cat:
                    noticias.append({
                        "t": e.title,
                        "l": e.link,
                        "f": f['n'],
                        "c": cat
                    })
    return noticias

# --- EJECUCIÓN ---
# El código se ejecuta cada vez que se carga la página
noticias_actuales = buscar_noticias()

# Botón manual por si acaso
if st.button('🔄 REFORZAR BÚSQUEDA MANUAL'):
    st.rerun()

# Diseño en 3 columnas
c1, c2, c3 = st.columns(3)
secciones = [("🐄 VACUNO", c1), ("🦆 AVES", c2), ("🐖 PORCINO", c3)]

for nombre_cat, col in secciones:
    with col:
        st.header(nombre_cat)
        titulos_vistos = set()
        filtradas = []
        for n in noticias_actuales:
            if n['c'] == nombre_cat and n['t'] not in titulos_vistos:
                filtradas.append(n)
                titulos_vistos.add(n['t'])
        
        if filtradas:
            # Mostramos las 20 últimas de cada categoría (sin límite de fecha)
            for n in filtradas[:20]:
                with st.container():
                    st.info(f"**{n['t']}**\n\n📍 Fuente: {n['f']}")
                    st.link_button("👉 LEER NOTICIA", n['l'])
                    st.divider()
        else:
            st.warning("Buscando en histórico... Si no aparece nada, es que la fuente no tiene registros.")
