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

1. Create a new Compose file in the OMV Compose plugin.
2. Paste `docker-compose.yml`.
3. Add the values from `.env.example` in the plugin's environment section, or upload a `.env` file beside the compose file.
4. Set `POSTGRES_PASSWORD` to a real password.
5. Deploy the stack.
6. Visit `http://<omv-host>:5173`.

If ports `5173` or `8000` are already taken on the OMV host, change `FRONTEND_PORT` or `BACKEND_PORT`.

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
