import streamlit as st
import feedparser
from datetime import datetime

# 1. Configuración de la App
st.set_page_config(page_title="Noticias Epizootias v2", layout="wide")

# Muestra la hora exacta de la consulta para que sepas que se ha actualizado
hora_actual = datetime.now().strftime("%H:%M:%S")
st.title("📱 Noticias Epizootias")
st.write(f"⏱️ Última comprobación en servidores: **{hora_actual}**")

# 2. FUENTES AMPLIADAS (8 Sitios distintos)
FUENTES = [
    {"n": "MAPA (Ministerio)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"},
    {"n": "Animals Health", "u": "https://www.animalshealth.es/rss/"},
    {"n": "Eurocarne", "u": "https://www.eurocarne.com/rss"},
    {"n": "3Tres3 (Cerdo)", "u": "https://www.3tres3.com/rss/noticias"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/"},
    {"n": "Agropopular", "u": "https://www.agropopular.com/feed/"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/"}
]

# Palabras clave (DNC, IAAP, PPA)
KEYWORDS = ["nodular", "dermatosis", "aviar", "iaap", "gripe", "peste", "ppa", "foco", "bovino", "cerdo", "vaca", "ave"]

def buscar_todo():
    resultados = []
    for f in FUENTES:
        try:
            d = feedparser.parse(f['u'])
            for e in d.entries:
                t = e.get('title', '').lower()
                if any(k in t for k in KEYWORDS):
                    # Clasificar
                    cat = "🔍 OTRAS"
                    if any(k in t for k in ["nodular", "dermatosis", "bovino", "vaca"]): cat = "🐄 VACUNO"
                    elif any(k in t for k in ["aviar", "iaap", "gripe", "ave"]): cat = "🦆 AVES"
                    elif any(k in t for k in ["peste", "ppa", "cerdo", "porcino"]): cat = "🐖 PORCINO"
                    
                    resultados.append({
                        "t": e.title,
                        "l": e.link,
                        "f": f['n'],
                        "c": cat
                    })
        except: continue
    return resultados

# --- BOTÓN DE ACTUALIZACIÓN REAL ---
if st.button('🔄 REESCANEAR FUENTES OFICIALES'):
    st.cache_data.clear()
    st.rerun()

noticias = buscar_todo()

# Columnas
c1, c2, c3 = st.columns(3)
categorias = [("🐄 VACUNO", c1), ("🦆 AVES", c2), ("🐖 PORCINO", c3)]

for nombre_cat, col in categorias:
    with col:
        st.header(nombre_cat)
        filtradas = [n for n in noticias if n['c'] == nombre_cat]
        if filtradas:
            for n in filtradas:
                st.info(f"**{n['t']}**\n\nFuente: {n['f']}")
                st.link_button("👉 LEER EN LA WEB", n['l'])
                st.divider()
        else:
            st.write("No hay noticias nuevas en esta sección.")
