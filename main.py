import streamlit as st
import feedparser

# Configuración de la App
st.set_page_config(page_title="Noticias Epizootias", page_icon="🧬", layout="wide")

st.title("📱 Noticias Epizootias")
st.markdown("### 🛰️ Últimas Alertas Sanitarias: España y Europa")
st.caption("Filtro especializado en DNC, Influenza Aviar y Peste Porcina")

# FUENTES DE DATOS (Direcciones verificadas)
FUENTES = [
    {"n": "MAPA (Ministerio España)", "u": "https://www.mapa.gob.es/es/prensa/ultimas-noticias/rss.aspx"},
    {"n": "Agrodigital", "u": "https://www.agrodigital.com/feed/"},
    {"n": "Animals Health", "u": "https://www.animalshealth.es/rss/"},
    {"n": "Eurocarne", "u": "https://www.eurocarne.com/rss"},
    {"n": "3Tres3 (Porcino)", "u": "https://www.3tres3.com/rss/noticias"},
    {"n": "Portal Veterinaria", "u": "https://www.portalveterinaria.com/rss/"}
]

# PALABRAS CLAVE (Lo que la app buscará)
KEYWORDS = ["nodular", "dermatosis", "aviar", "iaap", "gripe", "peste", "ppa", "asf", "foco", "bovino", "vaca", "ave", "cerdo"]

def cargar_noticias():
    noticias_finales = []
    
    for f in FUENTES:
        try:
            # Leemos el canal de noticias
            d = feedparser.parse(f['u'])
            
            for e in d.entries:
                titulo = e.get('title', '')
                link = e.get('link', '')
                
                # Buscamos si el título habla de lo que nos interesa
                t_low = titulo.lower()
                if any(k in t_low for k in KEYWORDS):
                    # Clasificación por sectores
                    cat = "🔍 OTROS"
                    if any(k in t_low for k in ["nodular", "dermatosis", "vaca", "bovino"]): cat = "🐄 VACUNO (DNC)"
                    elif any(k in t_low for k in ["aviar", "iaap", "gripe", "ave"]): cat = "🦆 AVES (IAAP)"
                    elif any(k in t_low for k in ["peste", "ppa", "asf", "cerdo"]): cat = "🐖 PORCINO (PPA)"
                    
                    noticias_finales.append({
                        "t": titulo,
                        "l": link,
                        "f": f['n'],
                        "c": cat
                    })
        except:
            continue
    return noticias_finales

# --- INTERFAZ ---
if st.button('🔄 ACTUALIZAR Y BUSCAR NUEVOS FOCOS'):
    st.cache_data.clear()

items = cargar_noticias()

# Creamos las 3 columnas
col1, col2, col3 = st.columns(3)
secciones = [("🐄 VACUNO (DNC)", col1), ("🦆 AVES (IAAP)", col2), ("🐖 PORCINO (PPA)", col3)]

for nombre_seccion, columna in secciones:
    with columna:
        st.header(nombre_seccion)
        # Filtramos las noticias de esta categoría
        filtradas = [n for n in items if n['c'] == nombre_seccion]
        
        if filtradas:
            for item in filtradas:
                with st.container():
                    st.write(f"📢 **{item['t']}**")
                    st.caption(f"📍 Fuente: {item['f']}")
                    # Botón directo a la noticia
                    st.link_button("👉 VER NOTICIA COMPLETA", item['l'])
                    st.divider()
        else:
            st.info("No se han encontrado noticias recientes en esta categoría.")

if not items:
    st.warning("No se han detectado noticias de epizootias en las fuentes consultadas hoy.")