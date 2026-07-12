# Noticias Epizootias

App en Streamlit para monitorizar noticias frescas en español sobre:

- DNC - Dermatitis Nodular Contagiosa
- IAAP - Influenza Aviar
- PPA - Peste Porcina Africana
- EN - Enfermedad de Newcastle

Ámbito priorizado:

- España
- Portugal
- Europa

## Funcionalidades

- Búsqueda automática de noticias en Google News RSS.
- Selección del número de días a revisar.
- Selección del número máximo de noticias por enfermedad.
- Actualización automática periódica.
- Visualización de noticias con enlace directo a la fuente.
- Selección manual de noticias para un informe.
- Generación de informe HTML corporativo con:
  - resumen automático,
  - resumen de fuentes seleccionadas,
  - listado de noticias con enlaces activos.

## Archivos necesarios

Coloca estos archivos en la misma carpeta que `main.py`:

- `Logo Nutreco.jpg`
- `Logo TechTeam 2.jpg`
- `Solapa rosa trasparente.png`

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run main.py
```

## Notas técnicas

- La app usa RSS de Google News en español.
- La actualización es periódica, no instantánea. Depende de la indexación de Google News.
- El informe HTML generado conserva la imagen corporativa y los enlaces web de las noticias seleccionadas.
