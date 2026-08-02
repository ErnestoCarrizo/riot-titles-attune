# Riot Titles Attune

Aplicación web en español para consultar el progreso de una cuenta de League of Legends hacia los títulos obtenibles mediante Desafíos. La app usa Riot ID (`Nombre#TAG`), convierte la cuenta a PUUID con `account-v1`, consulta `lol-challenges-v1` y construye el catálogo de títulos desde CommunityDragon.

## Requisitos

- Python 3.11 o superior.
- Una API key de Riot Games para consultar cuentas y desafíos.

Las development keys se obtienen desde el [Riot Developer Portal](https://developer.riotgames.com/). Expiran y deben renovarse con frecuencia. CommunityDragon no es una API oficial de Riot y sus esquemas pueden cambiar.

## Instalación y configuración

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
```

Completá `RIOT_API_KEY` en `.env`. La clave se usa únicamente en el backend y no se inicia ninguna llamada de Riot si falta; la API devuelve un error 503 claro al solicitar progreso.

## Ejecución

```bash
uvicorn app.main:app --reload
```

Abrí <http://127.0.0.1:8000>. También podés compartir una consulta con `/?riot_id=Nombre%23TAG&platform=LA2`.

## API

- `GET /api/health`
- `GET /api/platforms`
- `GET /api/titles?q=medicina&limit=50&offset=0`
- `GET /api/title-progress?riot_id=Nombre%23TAG&platform=LA2`
- `GET /api/title-tree?riot_id=Nombre%23TAG&platform=LA2&title_id=6e291d4d-a730-d2e0-c127-0ef0416c2977`

`/api/titles` es un catálogo puro y no conoce el estado de un jugador; por eso `status` solo acepta `all`. Los filtros de estado se aplican sobre la respuesta de progreso, tanto en la interfaz como en el navegador.

El catálogo consulta primero `es_ar` y usa `default` como fallback. Se mantiene en memoria durante seis horas por defecto y, si una recarga falla, se sirve la última versión válida como stale cache. El progreso de un jugador se cachea 60 segundos por plataforma y PUUID.

`/api/title-tree` devuelve el desglose recursivo de un título usando la jerarquía `tags.parent` de CommunityDragon. Cada nodo incluye sus hijos, estado, progreso, nivel actual, nivel objetivo y cuánto falta. En la interfaz aparece como “Ver desglose” en cada título; por ejemplo, “Dios de ARAM” muestra “Autoridad ARAM” y las ramas capstone que la componen.

Plataformas soportadas: `BR1`, `EUN1`, `EUW1`, `JP1`, `KR`, `LA1`, `LA2`, `NA1`, `OC1`, `TR1`, `RU`, `PH2`, `SG2`, `TH2`, `TW2`, `VN2`.

## Tests

```bash
pytest
```

Los tests usan fixtures JSON pequeños y mocks HTTP; no requieren una API key real ni acceso a internet.

La elección de Riot ID en vez del antiguo nombre de invocador sigue el endpoint vigente de cuentas: el nombre visible y el tag se resuelven con `account-v1`, que devuelve el PUUID necesario para consultar los desafíos.

## Frontend React

La interfaz vive en `frontend/` y usa React, TypeScript y Vite. Para reconstruir los assets que sirve FastAPI:

```bash
cd frontend
pnpm install
pnpm run build
```

El build se publica directamente en `app/static/`; el backend y sus endpoints no cambian.

## Texto legal

Este producto no está respaldado por Riot Games y no refleja las opiniones de Riot Games ni de ninguna persona involucrada oficialmente en la producción o gestión de sus propiedades. Riot Games y todas sus propiedades asociadas son marcas comerciales o marcas registradas de Riot Games, Inc.
