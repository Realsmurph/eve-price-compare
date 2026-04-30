from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import APP_ENV, APP_VERSION, CORS_ORIGINS, RUN_STATIC_DATA_LOADER
from .database import check_database
from .routers.market import router as market_router
from .routers.reactions import router as reactions_router
from .routers.watchlist import router as watchlist_router
from .services.static_data_loader import StaticDataLoader


@asynccontextmanager
async def lifespan(app: FastAPI):
    if RUN_STATIC_DATA_LOADER:
        StaticDataLoader().load()
    yield


app = FastAPI(
    title="eve-price-compare API",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if APP_ENV != "production" else None,
    redoc_url="/redoc" if APP_ENV != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["health"])
def readiness_check() -> dict[str, str]:
    check_database()
    return {"status": "ready"}


app.include_router(watchlist_router)
app.include_router(market_router)
app.include_router(reactions_router)
