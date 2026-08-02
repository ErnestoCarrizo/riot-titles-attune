# Deploy en Render Free

El archivo `render.yaml` configura un Web Service gratuito para esta aplicacion. Render instala `requirements.txt`, inicia FastAPI en el puerto `$PORT` y usa `/api/health` como health check.

1. Sube el repositorio a GitHub sin incluir `.env`.
2. En Render elige **New > Blueprint** y selecciona el repositorio.
3. Durante la creacion completa `RIOT_API_KEY` como secreto.
4. Confirma el plan **Free** y espera el primer deploy.

La API key debe configurarse desde Render. No debe aparecer en `render.yaml`, el frontend ni el historial de Git.
