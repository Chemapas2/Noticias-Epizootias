import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración de la App
st.set_page_config(page_title="Monitor Sanidad Animal", layout="wide")

st.title("🛰️ Monitor Sanidad Animal")
st.write(f"✅ Última actualización: **{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}**")

# 2. DEFINICIÓN DE FUENTES POR SECTOR
# Esto garantiza que siempre haya contenido
FUENTES_PORCINO = [
    "https://www.3tres3.com/rss/noticias",
    "https://www.eurocarne.com/rss",
    "https://www.portalveterinaria.com/rss/"
]

FUENTES_VACUNO = [
    "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx",
    "https://www.agrodigital.com/feed/",
    "https://efeagro.com/feed/"
]

FUENTES_AVES = [
    "https://www.avicultura.com/feed/",
    "https://www.agropopular.com/feed/",
    "https://www.interempresas.net/RSS/RssFicha.asp?IdF=64"
]

def cargar_rss(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return feedparser.parse(resp.read())
    except: return None

def mostrar_columna(titulo, urls, palabras_clave):
    st.header(titulo)
    noticias_encontradas = []
    
    for url in urls:
        feed = cargar_rss(url)
        if feed and feed.entries:
            for e in feed.entries:
                titulo_noticia = e.get('title', '')
                resumen = e.get('summary', e.get('description', '')).lower()
                
                # REGLA DE ORO: Si es una web especializada (como 3tres3), entra directo.
                # Si es general, buscamos palabras clave.
                if any(site in url for site in ["3tres3", "avicultura", "eurocarne"]) or \
                   any(k in (titulo_noticia + resumen).lower() for k in palabras_clave):
                    
                    noticias_encontradas.append({
                        "t": titulo_noticia,
                        "l": e.get('link', '#'),
                        "f": url.split('/')[2] # Nombre corto de la web
                    })
    
    # Mostrar resultados
    if noticias_encontradas:
        # Quitamos duplicados
        vistos = set()
        unicas = [n for n in noticias_encontradas if n['t'] not in vistos and not vistos.add(n['t'])]
        
        for n in unicas[:12]: # Mostramos las 12 últimas
            with st.container():
                st.info(f"**{n['t']}**")
                st.link_button("👉 LEER NOTICIA", n['l'])
                st.divider()
    else:
        st.write("☕ No se han detectado alertas hoy.")

# --- CUERPO DE LA APP ---
col1, col2, col3 = st.columns(3)

with col1:
    mostrar_columna("🐄 VACUNO", FUENTES_VACUNO, ["vaca", "vacuno", "bovino", "nodular", "dermatosis", "lengua azul", "ganado"])

with col2:
    mostrar_columna("🦆 AVES", FUENTES_AVES, ["aviar", "gripe", "ave", "pollo", "gallina", "huevo", "iaap"])

with col3:
    mostrar_columna("🐖 PORCINO", FUENTES_PORCINO, ["cerdo", "porcino", "peste", "ppa", "jamon", "embutido", "matadero", "lechon"])

if st.button('🔄 ACTUALIZAR AHORA'):
    st.rerun()
