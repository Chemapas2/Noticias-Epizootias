import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración
st.set_page_config(page_title="Monitor Sanidad", layout="wide")
st.title("🛰️ Monitor Sanidad Animal")
st.write(f"✅ Última actualización: {datetime.now().strftime('%H:%M:%S')}")

# 2. FUENTES POR SECTOR (Asignación directa)
FUENTES_VACUNO = ["https://www.agrodigital.com/feed/", "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"]
FUENTES_AVES = ["https://www.avicultura.com/feed/", "https://efeagro.com/feed/"]
FUENTES_PORCINO = ["https://www.3tres3.com/rss/noticias", "https://www.eurocarne.com/rss"]

# Palabras clave (ahora más abiertas)
K_VAC = ["vaca", "vacuno", "bovino", "leche", "nodular", "lengua azul", "ganado"]
K_AVE = ["aviar", "ave", "pollo", "gallina", "huevo", "gripe", "iaap"]
K_POR = ["cerdo", "porcino", "peste", "ppa", "lechon", "iberico", "matadero", "jamon", "carne"]

def traer_noticias(urls, keywords, forzar_todo=False):
    lista = []
    vistos = set()
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                f = feedparser.parse(resp.read())
                for e in f.entries:
                    t = e.get('title', '')
                    res = (t + " " + e.get('summary', '')).lower()
                    link = e.get('link', '#')
                    fuente_nombre = url.split('/')[2].replace('www.', '')

                    # Si forzamos (para 3tres3/avicultura) o si cumple keywords
                    if forzar_todo or any(k in res for k in keywords):
                        if t not in vistos:
                            lista.append({"t": t, "l": link, "f": fuente_nombre})
                            vistos.add(t)
        except: continue
    return lista

# --- PROCESO DE CARGA ---
# Para Porcino y Aves, "forzamos" la entrada de sus webs principales para que nunca estén vacías
noticias_porcino = traer_noticias(FUENTES_PORCINO, K_POR, forzar_todo=True)
noticias_vacuno = traer_noticias(FUENTES_VACUNO, K_VAC, forzar_todo=False)
noticias_aves = traer_noticias(FUENTES_AVES, K_AVE, forzar_todo=True)

# --- DISEÑO ---
c1, c2, c3 = st.columns(3)

with c1:
    st.header("🐄 VACUNO")
    if noticias_vacuno:
        for n in noticias_vacuno[:8]:
            st.info(f"**{n['t']}**\n\n📍 {n['f']}")
            st.link_button("👉 LEER", n['l'], key=n['l']+"vac")
            st.divider()
    else: st.write("Sin noticias.")

with c2:
    st.header("🦆 AVES")
    if noticias_aves:
        for n in noticias_aves[:8]:
            st.info(f"**{n['t']}**\n\n📍 {n['f']}")
            st.link_button("👉 LEER", n['l'], key=n['l']+"ave")
            st.divider()
    else: st.write("Sin noticias.")

with c3:
    st.header("🐖 PORCINO")
    # Si por algún motivo fallan las fuentes, metemos un backup de Agrodigital filtrado
    if len(noticias_porcino) < 3:
        backup = traer_noticias(["https://www.agrodigital.com/feed/"], K_POR)
        noticias_porcino.extend(backup)
    
    if noticias_porcino:
        for n in noticias_porcino[:8]:
            st.info(f"**{n['t']}**\n\n📍 {n['f']}")
            st.link_button("👉 LEER", n['l'], key=n['l']+"por")
            st.divider()
    else: st.write("Sin noticias.")

if st.button('🔄 RECARGAR TODO'):
    st.rerun()
