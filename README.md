# Noticias Epizootias

App en Streamlit para monitorizar noticias de los últimos 7 días sobre:

- DNC (Dermatitis Nodular Contagiosa)
- IAAP (Influenza Aviar de Alta Patogenicidad)
- PPA (Peste Porcina Africana)

Ámbito de búsqueda:

- España
- Portugal
- Europa

## Contenido del proyecto

- `main.py`: aplicación principal
- `requirements.txt`: dependencias
- `Logo Nutreco.jpg`: logo principal de marca
- `Logo TechTeam 2.jpg`: logo secundario
- `Solapa rosa.jpg`: cabecera gráfica

## Cómo ejecutar en local

```bash
pip install -r requirements.txt
streamlit run main.py
```

## Cómo funciona

- Consulta Google News RSS en español.
- Busca noticias publicadas en los últimos 7 días.
- Muestra hasta 5 noticias por enfermedad.
- Se refresca automáticamente cada 5 minutos.
- También permite actualización manual con el botón `Actualizar ahora`.

## Notas

- La actualización es periódica, no instantánea.
- La disponibilidad de noticias depende de la indexación de Google News.
- Los logos deben permanecer en la misma carpeta que `main.py`.
