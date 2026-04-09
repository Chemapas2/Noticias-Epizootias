import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración de la App
st.set_page_config(page_title="Monitor Sanidad Animal", layout="wide")

# Título y actualización automática
st.title("🛰️ Monitor Sanidad Animal y Ganadería")
st.write(f"✅ Datos actualizados: **{datetime.now().strftime('%H:%M:%S')}**")

# 2. FUENTES OFICIALES Y DE SECTOR
FUENTES = [
    {"n": "MAPA (Ministerio)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/"},
    {"n": "Eurocarne", "u": "https://www.eurocarne.com/rss"},
    {"n": "3Tres3 (Porcino)", "u": "https://www.3tres3.com/rss/noticias"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/"},
    {"n": "Agropopular", "u": "https://www.agropopular.com/feed/"}
]

# 3. DICCIONARIO RADAR (Ampliado para que siempre haya contenido)
PALABRAS_VACUNO = ["nodular", "dermatosis", "vaca", "vacuno", "bovino", "lengua azul", "ganado", "rumiante", "ternera", "leche"]
PALABRAS_AVES = ["aviar", "iaap", "gripe", "ave", "pollo", "gallina", "h5n1", "avícola", "huevo"]
PALABRAS_PORCINO = ["peste", "ppa", "asf", "cerdo", "porcino", "jabali", "lechon", "cárnico", "embutido", "jamon"]

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
                # Buscamos en título y resumen
                texto = (e.get('title', '') + " " + e.get('summary', '')).lower()
                
                cat = None
                if any(k in texto for k in PALABRAS_VACUNO): cat = "🐄 VACUNO"
                elif any(k in texto for k in PALABRAS_AVES): cat = "🦆 AVES"
                elif any(k in texto for k in PALABRAS_PORCINO): cat = "🐖 PORCINO"
                
                if cat:
                    noticias.append({
                        "t": e.title,
                        "l": e.link,
                        "f": f['n'],
                        "c": cat
                    })
    return noticias

# --- EJECUCIÓN AUTOMÁTICA ---
items = buscar_noticias()

# Botón por si el usuario quiere refrescar a mano
if st.button('🔄 RECARGAR AHORA'):
    st.rerun()

# Diseño en 3 columnas
c1, c2, c3 = st.columns(3)
secciones = [("🐄 VACUNO", c1), ("🦆 AVES", c2), ("🐖 PORCINO", c3)]

for nombre_cat, col in secciones:
    with col:
        st.header(nombre_cat)
        vistos = set()
        filtradas = [n for n in items if n['c'] == nombre_cat and n['t'] not in vistos and not vistos.add(n['t'])]
        
        if filtradas:
            for n in filtradas[:15]:
                with st.container():
                    st.info(f"**{n['t']}**\n\n📍 {n['f']}")
                    st.link_button("👉 ABRIR NOTICIA", n['l'])
                    st.divider()
        else:
            # En lugar de "Buscando...", ponemos un mensaje limpio
            st.write("☕ No hay noticias urgentes hoy en esta sección.")
