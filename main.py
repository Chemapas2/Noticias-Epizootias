import requests
from datetime import datetime

# --- CONFIGURACIÓN ---
API_KEY = "TU_API_KEY_AQUI"  # Sustituye por tu clave (ej. NewsAPI, Serper, etc.)
BASE_URL = "https://newsapi.org/v2/everything" # Ejemplo con NewsAPI

def obtener_noticias_porcino_economicas():
    """
    Busca noticias de porcino con un enfoque expandido a 
    consecuencias económicas y PPA.
    """
    
    # 1. Definimos una consulta robusta usando operadores OR y AND
    # Esto busca: (cerdo o porcino) Y (PPA o crisis o exportación o precio)
    query = (
        '(porcino OR cerdo OR "sector cárnico") AND '
        '("PPA" OR "peste porcina" OR "consecuencias económicas" OR '
        '"exportación" OR "precios" OR "aranceles" OR "mercado China")'
    )

    parametros = {
        'q': query,
        'language': 'es',        # Idioma español
        'sortBy': 'publishedAt', # Las más recientes primero
        'pageSize': 10,          # Cantidad de resultados
        'apiKey': API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=parametros)
        data = response.json()

        if data.get("status") == "ok" and data.get("totalResults", 0) > 0:
            return data["articles"]
        else:
            # Si no hay noticias hoy, lanzamos una búsqueda de backup más general
            return buscar_historico_economico()
            
    except Exception as e:
        print(f"Error en la conexión: {e}")
        return []

def buscar_historico_economico():
    """Búsqueda de seguridad para evitar que la pantalla salga vacía"""
    params_backup = {
        'q': 'economía porcina España PPA',
        'language': 'es',
        'apiKey': API_KEY
    }
    res = requests.get(BASE_URL, params=params_backup)
    return res.json().get("articles", [])

def main():
    print(f"--- Buscador de Actualidad Porcina (Fecha: {datetime.now().strftime('%d/%m/%Y')}) ---")
    
    noticias = obtener_noticias_porcino_economicas()
    
    if not noticias:
        # Este es el mensaje que intentamos evitar
        print("⚠️ No se encontraron noticias críticas hoy. Revisando histórico...")
    else:
        for idx, noticia in enumerate(noticias, 1):
            titulo = noticia.get('title')
            fuente = noticia.get('source', {}).get('name')
            url = noticia.get('url')
            
            print(f"\n[{idx}] {titulo}")
            print(f"    Fuente: {fuente}")
            print(f"    Link: {url}")

if __name__ == "__main__":
    main()
