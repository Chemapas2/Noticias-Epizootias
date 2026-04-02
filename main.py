import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

st.set_page_config(page_title="Alertas Epizootias v3", layout="wide")

st.title("🛰️ Monitor de Sanidad Animal (Versión Ampliada)")
st.write(f"⏱️ Consulta: **{datetime.now().strftime('%H:%M:%S')}**")

FUENTES = [
    {"n": "MAPA (Ministerio)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/"},
    {"n": "Eurocarne", "u": "https://www.eurocarne.com/rss"},
    {"n": "3Tres3 (Porcino)", "u": "https://www.3tres3.com/rss/noticias"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/"},
    {"n": "Agropopular", "u": "https://www.agropopular.com/feed/"}
]

# PALABRAS CLAVE MUCHO MÁS AMPLIAS
PALABRAS_VACUNO = ["nodular", "dermatosis", "vaca", "vacuno", "bovino", "lengua azul", "ganado", "rumiante", "explotación"]
PALABRAS_AVES = ["aviar", "iaap", "gripe", "ave", "pollo", "gallina", "h5n1", "explotación avícola"]
PALABRAS_PORCINO = ["peste", "ppa", "asf", "cerdo", "porcino", "jabali", "lechon", "cárnico", "matadero"]

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
                # Miramos en el título Y en el resumen (summary)
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
                        "c": cat,
                        "d": e.get('published', '')
                    })
    return noticias

if st.button('🔄 REESCANEAR TODO EL SECTOR GANADERO'):
    st.cache_data.clear()
    st.rerun()

todas = buscar_noticias()

c1, c2, c3 = st.columns(3)
secciones = [("🐄 VACUNO", c1), ("🦆 AVES", c2), ("🐖 PORCINO", c3)]

for nombre_cat, col in secciones:
    with col:
        st.header(nombre_cat)
        # Eliminamos duplicados por título
        titulos_vistos = set()
        filtradas = []
        for n in todas:
            if n['c'] == nombre_cat and n['t'] not in titulos_vistos:
                filtradas.append(n)
                titulos_vistos.add(n['t'])
        
        if filtradas:
            for n in filtradas[:15]: # Mostramos hasta 15 noticias
                st.info(f"**{n['t']}**\n\n📍 Fuente: {n['f']}")
                st.link_button("👉 LEER NOTICIA", n['l'])
                st.divider()
        else:
            st.write("No hay menciones recientes en los boletines.")
