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

Start the stack:

```bash
docker compose up -d --build
```

Open the frontend:

```text
http://localhost:5173
```

Backend healthcheck:

```text
http://localhost:8000/health
```

The frontend proxies API calls through nginx, so browser calls use the same origin:

- `/api/items/search?q=tri`
- `/api/items/compare?type_id=34`
- `/api/reactions/16659`
- `/watchlist`

## OpenMediaVault Compose Plugin

If you paste only a compose file into OMV, use `docker-compose.omv.yml`. It pulls prebuilt images from GitHub Container Registry and does not require OMV to build the app locally.

1. Create a new Compose file in the OMV Compose plugin.
2. Paste `docker-compose.omv.yml`.
3. Add the values from `.env.example` in the plugin's environment section, or upload a `.env` file beside the compose file.
4. Set `POSTGRES_PASSWORD` to a real password.
5. Deploy the stack.
6. Visit `http://<omv-host>:5173`.

If ports `5173` or `8000` are already taken on the OMV host, change `FRONTEND_PORT` or `BACKEND_PORT`.

To update after a new GitHub commit, pull the latest images and recreate the containers from OMV, or run:

```bash
docker compose -f docker-compose.omv.yml pull
docker compose -f docker-compose.omv.yml up -d
```

Images are published by GitHub Actions:

- `ghcr.io/realsmurph/eve-price-compare-backend:latest`
- `ghcr.io/realsmurph/eve-price-compare-frontend:latest`

Use `docker-compose.yml` only when the full repository has been cloned locally and the compose file sits beside the `backend/` and `frontend/` directories.

## Local Backend Development

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd ..
uvicorn backend.app:app --reload
```

## Local Frontend Development

```bash
cd frontend
npm install
npm run dev
```

For local Vite development, set `VITE_API_BASE_URL=http://localhost:8000` if you run the frontend outside Docker.
