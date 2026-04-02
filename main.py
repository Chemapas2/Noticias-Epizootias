import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración
st.set_page_config(page_title="Alertas Epizootias v2", layout="wide")

st.title("🛰️ Monitor de Sanidad Animal")
st.write(f"⏱️ Última consulta a fuentes: **{datetime.now().strftime('%H:%M:%S')}**")

# 2. FUENTES (Sin Animals Health, con Agrodigital y Ministerio)
FUENTES = [
    {"n": "MAPA (Ministerio España)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/"},
    {"n": "Eurocarne (Cárnico)", "u": "https://www.eurocarne.com/rss"},
    {"n": "3Tres3 (Porcino)", "u": "https://www.3tres3.com/rss/noticias"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/"}
]

# 3. DICCIONARIO AMPLIADO (Para que no se escape nada)
# He añadido sinónimos para asegurar que las columnas de PPA y DNC se llenen.
PALABRAS_VACUNO = ["nodular", "dermatosis", "vaca", "vacuno", "bovino", "lengua azul", "ehp"]
PALABRAS_AVES = ["aviar", "iaap", "gripe", "ave", "pollo", "gallina", "h5n1"]
PALABRAS_PORCINO = ["peste", "ppa", "asf", "cerdo", "porcino", "jabali", "lechon"]

def cargar_datos_seguro(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return feedparser.parse(response.read())
    except:
        return None

def buscar_noticias():
    noticias = []
    for f in FUENTES:
        d = cargar_datos_seguro(f['u'])
        if d and d.entries:
            for e in d.entries:
                t = e.get('title', '').lower()
                
                # Clasificación Inteligente
                cat = None
                if any(k in t for k in PALABRAS_VACUNO): cat = "🐄 VACUNO (DNC/Otras)"
                elif any(k in t for k in PALABRAS_AVES): cat = "🦆 AVES (IAAP)"
                elif any(k in t for k in PALABRAS_PORCINO): cat = "🐖 PORCINO (PPA)"
                
                if cat:
                    noticias.append({
                        "t": e.title,
                        "l": e.link,
                        "f": f['n'],
                        "c": cat
                    })
    return noticias

# --- BOTÓN DE ACTUALIZACIÓN ---
if st.button('🔄 BUSCAR ÚLTIMAS ALERTAS EN TODO EL SECTOR'):
    st.cache_data.clear()
    st.rerun()

todas = buscar_noticias()

# Diseño en 3 columnas
c1, c2, c3 = st.columns(3)
secciones = [("🐄 VACUNO (DNC/Otras)", c1), ("🦆 AVES (IAAP)", c2), ("🐖 PORCINO (PPA)", c3)]

for nombre_cat, col in secciones:
    with col:
        st.header(nombre_cat)
        filtradas = [n for n in todas if n['c'] == nombre_cat]
        if filtradas:
            # Mostramos las 10 más recientes de cada categoría
            for n in filtradas[:10]:
                st.info(f"**{n['t']}**\n\n📍 Fuente: {n['f']}")
                st.link_button("👉 VER NOTICIA COMPLETA", n['l'])
                st.divider()
        else:
            st.write("No hay noticias recientes con estas palabras clave.")

if not todas:
    st.warning("No se han encontrado noticias hoy. Es posible que los medios no hayan publicado alertas en las últimas horas.")
