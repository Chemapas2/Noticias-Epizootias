import streamlit as st
import feedparser
import urllib.request
from datetime import datetime

# 1. Configuración de la App
st.set_page_config(page_title="Monitor Sanidad Animal", layout="wide")

st.title("🛰️ Monitor Sanidad Animal")
st.write(f"✅ Filtros de precisión aplicados | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# 2. FUENTES CLASIFICADAS POR FIABILIDAD
FUENTES = [
    {"n": "3Tres3 (Especialista Porcino)", "u": "https://www.3tres3.com/rss/noticias", "pref": "PORCINO"},
    {"n": "Eurocarne (Sector Cárnico)", "u": "https://www.eurocarne.com/rss", "pref": "PORCINO"},
    {"n": "Ministerio (MAPA)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx", "pref": "MIXTO"},
    {"n": "Avicultura.com", "u": "https://www.avicultura.com/feed/", "pref": "AVES"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/", "pref": "MIXTO"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/", "pref": "MIXTO"},
    {"n": "EfeAgro", "u": "https://efeagro.com/feed/", "pref": "AGENCIA"}
]

# Palabras clave de alta precisión
KEYWORDS_VACUNO = ["vaca", "vacuno", "bovino", "nodular", "dermatosis", "lengua azul", "leche", "rumiante"]
KEYWORDS_AVES = ["aviar", "iaap", "gripe", "ave", "pollo", "gallina", "huevo", "avicultura"]
KEYWORDS_PORCINO = ["cerdo", "porcino", "peste", "ppa", "asf", "lechon", "iberico", "porcina", "jabali"]

def cargar_rss(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return feedparser.parse(resp.read())
    except: return None

def obtener_noticias():
    # Estructura: almacen[categoría] = {fuente: [noticias]}
    almacen = {
        "🐄 VACUNO": {f['n']: [] for f in FUENTES},
        "🦆 AVES": {f['n']: [] for f in FUENTES},
        "🐖 PORCINO": {f['n']: [] for f in FUENTES}
    }
    
    for f in FUENTES:
        feed = cargar_rss(f['u'])
        if feed and feed.entries:
            for e in feed.entries:
                titulo = e.get('title', '')
                resumen = (e.get('summary', e.get('description', ''))).lower()
                texto_total = (titulo + " " + resumen).lower()
                
                cat = None
                # LÓGICA DE CLASIFICACIÓN ESTRICTA
                if any(k in texto_total for k in KEYWORDS_PORCINO) or (f['pref'] == "PORCINO" and "noticia" in texto_total):
                    cat = "🐖 PORCINO"
                elif any(k in texto_total for k in KEYWORDS_VACUNO):
                    cat = "🐄 VACUNO"
                elif any(k in texto_total for k in KEYWORDS_AVES) or f['pref'] == "AVES":
                    cat = "🦆 AVES"
                
                if cat:
                    almacen[cat][f['n']].append({"t": titulo, "l": e.get('link', '#'), "f": f['n']})
    
    # REPARTO EQUITATIVO (Round Robin) para evitar que EfeAgro domine
    resultado = {"🐄 VACUNO": [], "🦆 AVES": [], "🐖 PORCINO": []}
    for cat in almacen:
        for i in range(15): # Capas de profundidad
            for f in FUENTES:
                # Si la fuente es EfeAgro y ya tenemos noticias, no le damos prioridad
                if f['n'] == "EfeAgro" and i == 0 and len(almacen[cat][f['n']]) > 0:
                    continue 
                if len(almacen[cat][f['n']]) > i:
                    resultado[cat].append(almacen[cat][f['n']][i])
    
    return resultado

# --- INTERFAZ ---
datos = obtener_noticias()
col1, col2, col3 = st.columns(3)

secciones = [("🐄 VACUNO", col1), ("🦆 AVES", col2), ("🐖 PORCINO", col3)]

for nombre_cat, columna in secciones:
    with columna:
        st.header(nombre_cat)
        lista = datos[nombre_cat]
        
        if len(lista) > 0:
            # Mostramos las noticias diversificadas
            vistos = set()
            count = 0
            for n in lista:
                if n['t'] not in vistos and count < 8:
                    with st.container():
                        st.info(f"**{n['t']}**\n\n📍 Fuente: {n['f']}")
                        st.link_button("👉 LEER NOTICIA", n['l'], key=n['l']+nombre_cat+str(count))
                        st.divider()
                        vistos.add(n['t'])
                        count += 1
        else:
            st.warning("Sin noticias específicas hoy.")

if st.button('🔄 REESCANEAR AHORA'):
    st.rerun()
