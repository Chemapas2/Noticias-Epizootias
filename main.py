import streamlit as st
import feedparser
import urllib.request
import random
from datetime import datetime

# 1. Configuración
st.set_page_config(page_title="Monitor Sanidad", layout="wide")
st.title("🛰️ Monitor Sanidad Animal")
st.write(f"✅ Actualización: {datetime.now().strftime('%H:%M:%S')}")

# 2. FUENTES REORGANIZADAS (Cada una a su sitio)
FUENTES_PORCINO = ["https://www.3tres3.com/rss/noticias", "https://www.eurocarne.com/rss"]
FUENTES_VACUNO = ["https://www.agrodigital.com/category/ganaderia/vacuno/feed/", "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"]
FUENTES_AVES = ["https://www.avicultura.com/feed/", "https://www.portalveterinaria.com/rss/"]
FUENTES_GENERAL = ["https://efeagro.com/feed/"]

# Palabras clave de limpieza (Estrictas)
K_POR = ["cerdo", "porcino", "peste", "ppa", "lechon", "iberico", "matadero", "jamon", "porcina"]
K_VAC = ["vaca", "vacuno", "bovino", "leche", "nodular", "lengua azul", "ternera"]
K_AVE = ["aviar", "ave", "pollo", "gallina", "huevo", "gripe", "iaap"]

def traer_datos(urls, keywords, forzar=False):
    lista = []
    vistos = set()
    # User-Agents variados para evitar el error de conexión (bloqueo)
    agentes = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    ]
    
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': random.choice(agentes)})
            with urllib.request.urlopen(req, timeout=15) as resp:
                f = feedparser.parse(resp.read())
                for e in f.entries:
                    t = e.get('title', '')
                    res = (t + " " + e.get('summary', '')).lower()
                    link = e.get('link', '#')
                    # Solo entra si es fuente forzada O si cumple la palabra clave exacta
                    if forzar or any(k in res for k in keywords):
                        if t not in vistos:
                            lista.append({"t": t, "l": link, "f": url.split('/')[2]})
                            vistos.add(t)
        except: continue
    return lista

# --- CARGA DE DATOS ---
noticias_p = traer_datos(FUENTES_PORCINO, K_POR, forzar=True)
noticias_v = traer_datos(FUENTES_VACUNO, K_VAC, forzar=True)
noticias_a = traer_datos(FUENTES_AVES, K_AVE, forzar=True)

# Si faltan noticias (menos de 5), buscamos en EfeAgro pero SOLO con filtro estricto
if len(noticias_p) < 5: noticias_p.extend(traer_datos(FUENTES_GENERAL, K_POR)[:5])
if len(noticias_v) < 5: noticias_v.extend(traer_datos(FUENTES_GENERAL, K_VAC)[:5])
if len(noticias_a) < 5: noticias_a.extend(traer_datos(FUENTES_GENERAL, K_AVE)[:5])

# --- DISEÑO ---
c1, c2, c3 = st.columns(3)

def renderizar(columna, titulo, lista):
    with columna:
        st.header(titulo)
        if lista:
            for n in lista[:6]: # Mostramos las 6 mejores
                with st.container():
                    st.info(f"**{n['t']}**\n\n📍 {n['f']}")
                    st.link_button("👉 LEER", n['l'], key=n['l']+titulo)
                    st.divider()
        else:
            st.warning("Buscando noticias... Reintente en unos segundos.")

renderizar(c1, "🐄 VACUNO", noticias_v)
renderizar(c2, "🦆 AVES", noticias_a)
renderizar(c3, "🐖 PORCINO", noticias_p)

if st.button('🔄 REINTENTAR CONEXIÓN'):
    st.rerun()
