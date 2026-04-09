import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración de la App
st.set_page_config(page_title="Monitor Sanidad Animal", layout="wide")

st.title("🛰️ Monitor Sanidad Animal")
st.write(f"✅ Última actualización del sistema: **{datetime.now().strftime('%H:%M:%S')}**")

# 2. FUENTES RSS
FUENTES = [
    {"n": "MAPA (Ministerio)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/"},
    {"n": "Eurocarne", "u": "https://www.eurocarne.com/rss"},
    {"n": "3Tres3 (Cerdo)", "u": "https://www.3tres3.com/rss/noticias"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/"}
]

# Palabras clave
PALABRAS_VACUNO = ["nodular", "dermatosis", "vaca", "vacuno", "bovino", "lengua azul", "ganado", "ehp"]
PALABRAS_AVES = ["aviar", "iaap", "gripe", "ave", "pollo", "gallina", "avícola"]
PALABRAS_PORCINO = ["peste", "ppa", "asf", "cerdo", "porcino", "jabali", "lechon", "africana"]

def cargar_rss(url):
    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        with opener.open(url, timeout=20) as response:
            return feedparser.parse(response.read())
    except: return None

def obtener_alertas():
    noticias = []
    for f in FUENTES:
        feed = cargar_rss(f['u'])
        if feed and feed.entries:
            for e in feed.entries:
                contenido = (e.get('title', '') + " " + e.get('summary', '')).lower()
                cat = None
                if any(k in contenido for k in PALABRAS_VACUNO): cat = "🐄 VACUNO"
                elif any(k in contenido for k in PALABRAS_AVES): cat = "🦆 AVES"
                elif any(k in contenido for k in PALABRAS_PORCINO): cat = "🐖 PORCINO"
                if cat:
                    noticias.append({"t": e.title, "l": e.link, "f": f['n'], "c": cat})
    return noticias

# --- INTERFAZ ---
items = obtener_alertas()

col1, col2, col3 = st.columns(3)

# Configuración de las secciones con sus enlaces permanentes al histórico
secciones = [
    {
        "titulo": "🐄 VACUNO",
        "col": col1,
        "historia": "https://www.mapa.gob.es/es/ganaderia/temas/sanidad-animal-higiene-ganadera/sanidad-animal/enfermedades/dermatosis-nodular-contagiosa/DNC.aspx",
        "keywords": PALABRAS_VACUNO
    },
    {
        "titulo": "🦆 AVES",
        "col": col2,
        "historia": "https://www.mapa.gob.es/es/ganaderia/temas/sanidad-animal-higiene-ganadera/sanidad-animal/enfermedades/influenza-aviar/influenza_aviar.aspx",
        "keywords": PALABRAS_AVES
    },
    {
        "titulo": "🐖 PORCINO",
        "col": col3,
        "historia": "https://www.mapa.gob.es/es/ganaderia/temas/sanidad-animal-higiene-ganadera/sanidad-animal/enfermedades/peste-porcina-africana/peste_porcina_africana.aspx",
        "keywords": PALABRAS_PORCINO
    }
]

for s in secciones:
    with s['col']:
        st.header(s['titulo'])
        
        # 1. Mostrar noticias automáticas si las hay
        filtradas = [n for n in items if n['c'] == s['titulo']]
        if filtradas:
            for n in filtradas[:10]:
                st.info(f"**{n['t']}**\n\n📍 {n['f']}")
                st.link_button("👉 VER NOTICIA", n['l'])
                st.divider()
        
        # 2. SIEMPRE mostrar el acceso al histórico oficial
        st.write("---")
        st.subheader("📚 Histórico y Situación")
        st.write(f"Consulta los últimos informes oficiales y la situación epidemiológica de {s['titulo'].lower()}:")
        st.link_button(f"🔎 INFORME OFICIAL {s['titulo']}", s['historia'])
