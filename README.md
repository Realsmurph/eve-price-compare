# eve-price-compare

Full-stack MVP for comparing EVE market prices, managing a watchlist, searching static item data, and calculating reaction profit.

## Services

- FastAPI backend
- Postgres database
- React/Vite frontend served by nginx
- Docker Compose deployment

## Run With Docker Compose

Copy the example environment file and adjust the password:

```bash
cp .env.example .env
```

Start the stack using prebuilt images:

```bash
docker compose pull
docker compose up -d
```

Open the frontend:

```text
http://localhost:5173
```

Backend healthcheck:

```text
http://localhost:8005/health
```

The frontend proxies API calls through nginx, so browser calls use the same origin:

- `/api/items/search?q=tri`
- `/api/items/search?q=rifter&category=Ship`
- `/api/items/compare?type_id=34`
- `/api/items/34/history`
- `/api/reactions/16659`
- `/watchlist`

## Static Data And Price History

On startup, the backend loads static item data. By default it downloads Fuzzwork SDE CSV files from:

```text
https://www.fuzzwork.co.uk/dump/latest
```

It imports published market items, group/category metadata, item volume, and activity `11` reaction recipes. If Fuzzwork is unavailable, the app still boots with the bundled mock seed data.

Refresh static data manually inside the backend container:

```bash
docker compose exec backend python -m backend.commands.refresh_static_data --force
```

Market compares store Jita, Amarr, and C-J snapshots in `market_price_history`. You can also run a batch refresh:

```bash
docker compose exec backend python -m backend.commands.refresh_price_history --limit 250
```

For ESI daily market history, use:

```bash
docker compose exec backend python -m backend.commands.refresh_price_history --daily --limit 250
```

Use `--all-items` with a sensible `--limit` when you want to walk the full marketable catalog. ESI rate limits still apply, so schedule large refreshes gradually.

## OpenMediaVault Compose Plugin

If you paste only a compose file into OMV, use `docker-compose.omv.yml`. It pulls prebuilt images from GitHub Container Registry and does not require OMV to build the app locally.

1. Create a new Compose file in the OMV Compose plugin.
2. Paste `docker-compose.omv.yml`.
3. Add the values from `.env.example` in the plugin's environment section, or upload a `.env` file beside the compose file.
4. Set `POSTGRES_PASSWORD` to a real password.
5. Deploy the stack.
6. Visit `http://<omv-host>:5173`.

If ports `5173` or `8005` are already taken on the OMV host, change `FRONTEND_PORT` or `BACKEND_PORT`.
The frontend container proxies API requests internally, so the backend does not need to be exposed publicly unless you want direct API access.

To update after a new GitHub commit, pull the latest images and recreate the containers from OMV, or run:

```bash
docker compose -f docker-compose.omv.yml pull
docker compose -f docker-compose.omv.yml up -d
```

Images are published by GitHub Actions:

- `ghcr.io/realsmurph/eve-price-compare-backend:latest`
- `ghcr.io/realsmurph/eve-price-compare-frontend:latest`

Use `docker-compose.local.yml` only when the full repository has been cloned locally and you want to build images from source on that machine:

```bash
docker compose -f docker-compose.local.yml up -d --build
```

## Local Backend Development

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd ..
uvicorn backend.app:app --reload
```

Run migrations manually:

```bash
alembic upgrade head
```

## Local Frontend Development

```bash
cd frontend
npm install
npm run dev
```

For local Vite development, set `VITE_API_BASE_URL=http://localhost:8000` if you run the frontend outside Docker.
