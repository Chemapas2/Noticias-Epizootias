import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración de la App
st.set_page_config(page_title="Noticias Epizootias v2", layout="wide")

# Muestra la hora de consulta para confirmar que la app está viva
st.title("📱 Monitor de Epizootias")
st.write(f"⏱️ Última actualización: **{datetime.now().strftime('%H:%M:%S')}**")

# 2. FUENTES SELECCIONADAS (Incluye Agrodigital, Excluye Animals Health)
FUENTES = [
    {"n": "MAPA (Ministerio España)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/"},
    {"n": "Eurocarne (Sector Cárnico)", "u": "https://www.eurocarne.com/rss"},
    {"n": "3Tres3 (Sector Porcino)", "u": "https://www.3tres3.com/rss/noticias"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/"}
]

# Palabras clave de búsqueda (Ajustadas para Sanidad Animal)
KEYWORDS = ["nodular", "dermatosis", "aviar", "iaap", "gripe", "peste", "ppa", "foco", "bovino", "cerdo", "vaca", "ave", "sanidad"]

def cargar_datos_seguro(url):
    """Función para evitar bloqueos de servidores oficiales"""
    try:
        # Nos identificamos como un navegador estándar
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=12) as response:
            return feedparser.parse(response.read())
    except:
        return None

def buscar_noticias():
    todas = []
    for f in FUENTES:
        d = cargar_datos_seguro(f['u'])
        if d and d.entries:
            for e in d.entries:
                titulo = e.get('title', '').lower()
                # Filtrado por palabras clave
                if any(k in titulo for k in KEYWORDS):
                    # Clasificación por categoría
                    cat = "🔍 OTRAS"
                    if any(k in titulo for k in ["nodular", "dermatosis", "vaca", "bovino"]): cat = "🐄 VACUNO"
                    elif any(k in titulo for k in ["aviar", "iaap", "gripe", "ave"]): cat = "🦆 AVES"
                    elif any(k in titulo for k in ["peste", "ppa", "cerdo", "porcino"]): cat = "🐖 PORCINO"
                    
                    todas.append({
                        "t": e.title,
                        "l": e.link,
                        "f": f['n'],
                        "c": cat
                    })
    return todas

# --- INTERFAZ ---
if st.button('🔄 REESCANEAR TODAS LAS FUENTES'):
    st.cache_data.clear()
    st.rerun()

noticias = buscar_noticias()

# Diseño en 3 columnas
col1, col2, col3 = st.columns(3)
secciones = [("🐄 VACUNO", col1), ("🦆 AVES", col2), ("🐖 PORCINO", col3)]

for nombre_cat, col in secciones:
    with col:
        st.header(nombre_cat)
        filtradas = [n for n in noticias if n['c'] == nombre_cat]
        if filtradas:
            for n in filtradas:
                # Caja de información visual
                st.info(f"**{n['t']}**\n\n📍 Fuente: {n['f']}")
                # Botón de enlace directo
                st.link_button("👉 LEER NOTICIA COMPLETA", n['l'])
                st.divider()
        else:
            st.write("Sin novedades recientes en esta categoría.")

if not noticias:
    st.warning("No se han encontrado noticias específicas hoy. Prueba a darle al botón de reescanear.")
