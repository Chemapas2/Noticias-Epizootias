import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración de pantalla
st.set_page_config(page_title="Monitor Sanidad", layout="wide")
st.title("🛰️ Monitor Sectorial Ganadero")
st.write(f"✅ Actualización forzada: {datetime.now().strftime('%H:%M:%S')}")

# 2. ASIGNACIÓN DIRECTA DE FUENTES (Para asegurar contenido en cada columna)
# Cada columna tiene sus propias webs. No se mezclan.
FUENTES = {
    "🐄 VACUNO": [
        "https://www.agrodigital.com/category/ganaderia/vacuno/feed/",
        "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx",
        "https://efeagro.com/ganaderia/feed/"
    ],
    "🦆 AVES": [
        "https://www.avicultura.com/feed/",
        "https://efeagro.com/avicola/feed/",
        "https://www.portalveterinaria.com/rss/"
    ],
    "🐖 PORCINO": [
        "https://www.3tres3.com/rss/noticias",
        "https://www.eurocarne.com/rss",
        "https://www.agrodigital.com/category/ganaderia/porcino/feed/"
    ]
}

def traer_noticias_columna(urls):
    lista_noticias = []
    titulos_vistos = set()
    
    for url in urls:
        try:
            # Simulamos navegador para evitar bloqueos
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                f = feedparser.parse(resp.read())
                for e in f.entries:
                    t = e.get('title', '')
                    # Evitamos repetidos y noticias vacías
                    if t and t not in titulos_vistos:
                        lista_noticias.append({
                            "t": t,
                            "l": e.get('link', '#'),
                            "f": url.split('/')[2].replace('www.', '')
                        })
                        titulos_vistos.add(t)
        except:
            continue
    return lista_noticias

# --- PROCESO DE CARGA Y RENDERIZADO ---
col1, col2, col3 = st.columns(3)
columnas_st = [col1, col2, col3]

for i, (nombre_cat, urls) in enumerate(FUENTES.items()):
    with columnas_st[i]:
        st.header(nombre_cat)
        
        # Obtenemos todas las noticias de las fuentes de esa columna
        noticias = traer_noticias_columna(urls)
        
        # FORZAMOS: Mostramos las 5 primeras que encuentre, sin filtros de palabras
        if len(noticias) >= 1:
            # Seleccionamos las 5 más recientes
            for n in noticias[:5]:
                with st.container():
                    st.info(f"**{n['t']}**\n\n📍 Fuente: {n['f']}")
                    st.link_button("👉 LEER NOTICIA", n['l'], key=n['l']+nombre_cat)
                    st.divider()
        else:
            st.error("Error de conexión con la fuente. Reintente.")

if st.button('🔄 REFRESCAR TODO EL SISTEMA'):
    st.rerun()
