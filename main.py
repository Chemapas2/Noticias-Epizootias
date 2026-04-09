import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración de la App
st.set_page_config(page_title="Monitor Sanidad Animal", layout="wide")

st.title("🛰️ Monitor Sanidad Animal")
st.write(f"✅ Fuentes Diversificadas | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# 2. FUENTES ORGANIZADAS POR RELEVANCIA
FUENTES = [
    {"n": "Ministerio (MAPA)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"},
    {"n": "Eurocarne", "u": "https://www.eurocarne.com/rss"},
    {"n": "3Tres3 (Porcino)", "u": "https://www.3tres3.com/rss/noticias"},
    {"n": "Avicultura", "u": "https://www.avicultura.com/feed/"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/"}
]

# Palabras clave de clasificación
P_VACUNO = ["vaca", "vacuno", "bovino", "nodular", "dermatosis", "lengua azul", "ganado", "leche"]
P_AVES = ["aviar", "iaap", "gripe", "ave", "pollo", "gallina", "huevo", "avicultura"]
P_PORCINO = ["cerdo", "porcino", "peste", "ppa", "asf", "lechon", "ibérico", "cárnico"]

def cargar_rss(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return feedparser.parse(resp.read())
    except: return None

def obtener_noticias_mezcladas():
    # Diccionario para agrupar noticias por FUENTE y luego por CATEGORÍA
    # Estructura: pool[Categoría][Fuente] = [Lista de noticias]
    pool = {
        "🐄 VACUNO": {f['n']: [] for f in FUENTES},
        "🦆 AVES": {f['n']: [] for f in FUENTES},
        "🐖 PORCINO": {f['n']: [] for f in FUENTES}
    }
    
    for f in FUENTES:
        feed = cargar_rss(f['u'])
        if feed and feed.entries:
            for e in feed.entries:
                titulo = e.get('title', '')
                resumen = (e.get('summary', '') + " " + e.get('description', '')).lower()
                texto = (titulo + " " + resumen).lower()
                
                cat = None
                if any(k in texto for k in P_PORCINO) or "3tres3" in f['u']: cat = "🐖 PORCINO"
                elif any(k in texto for k in P_VACUNO): cat = "🐄 VACUNO"
                elif any(k in texto for k in P_AVES) or "avicultura" in f['u']: cat = "🦆 AVES"
                
                if cat:
                    pool[cat][f['n']].append({"t": titulo, "l": e.get('link', '#'), "f": f['n']})
    
    # Ahora mezclamos: cogemos la 1ª de cada fuente, luego la 2ª...
    resultado_final = {"🐄 VACUNO": [], "🦆 AVES": [], "🐖 PORCINO": []}
    
    for cat in resultado_final.keys():
        for i in range(10): # Intentamos sacar hasta 10 niveles de profundidad
            for f in FUENTES:
                if len(pool[cat][f['n']]) > i:
                    resultado_final[cat].append(pool[cat][f['n']][i])
                    
    return resultado_final

# --- MOSTRAR INTERFAZ ---
dict_noticias = obtener_noticias_mezcladas()
col1, col2, col3 = st.columns(3)

secciones = [
    ("🐄 VACUNO", col1),
    ("🦆 AVES", col2),
    ("🐖 PORCINO", col3)
]

for nombre_cat, columna in secciones:
    with columna:
        st.header(nombre_cat)
        lista = dict_noticias[nombre_cat]
        
        if lista:
            # Mostramos las 8 primeras (que estarán mezcladas de distintas fuentes)
            for n in lista[:8]:
                with st.container():
                    st.info(f"**{n['t']}**\n\n📍 Fuente: {n['f']}")
                    st.link_button("👉 LEER NOTICIA", n['l'], key=n['l']+nombre_cat)
                    st.divider()
        else:
            st.write("No hay noticias recientes.")

if st.button('🔄 ACTUALIZAR FUENTES'):
    st.rerun()
