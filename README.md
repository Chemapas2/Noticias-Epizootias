# Noticias Epizootias

App en Streamlit para monitorizar noticias en español sobre tres epizootias:

- DNC — Dermatitis Nodular Contagiosa
- IAAP — Influenza Aviar Altamente Patógena
- PPA — Peste Porcina Africana

El monitor busca noticias relacionadas con España, Portugal y Europa, usando Google News RSS, y muestra hasta 5 noticias por enfermedad.

## Funcionalidades

- Selección del número de días a buscar desde la barra lateral
- Actualización automática cada 5 minutos mientras la app está abierta
- Botón de actualización manual
- Identidad visual con logos de Nutreco y TechTeam
- Descarga de resultados en CSV
- Interfaz separada por pestañas para cada enfermedad

## Archivos necesarios

Coloca estos archivos en la misma carpeta:

- `main.py`
- `requirements.txt`
- `Logo Nutreco.jpg`
- `Logo TechTeam 2.jpg`
- `Solapa rosa.jpg`

## requirements.txt

```txt
streamlit>=1.37
```

## Cómo ejecutarla en local

```bash
pip install -r requirements.txt
streamlit run main.py
```

## Cómo usarla

1. Abre la barra lateral.
2. Selecciona cuántos días atrás quieres buscar.
3. La app consultará noticias de DNC, IAAP y PPA.
4. Si quieres, pulsa `Actualizar ahora`.
5. Puedes descargar el estado actual en CSV.

## Despliegue en Streamlit Community Cloud

1. Sube los archivos a un repositorio en GitHub.
2. Crea una app en Streamlit Community Cloud.
3. Selecciona el repositorio y el archivo `main.py`.
4. Verifica que los logos estén en la raíz del proyecto.

## Observaciones

- La actualización no es en tiempo real puro. La app vuelve a consultar periódicamente la fuente RSS.
- La disponibilidad de noticias depende de la indexación de Google News.
- El filtrado geográfico se basa en términos presentes en titular, resumen o medio.
