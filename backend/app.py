from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers.market import router as market_router
from .routers.reactions import router as reactions_router
from .routers.watchlist import router as watchlist_router
from .services.static_data_loader import StaticDataLoader


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    StaticDataLoader().load()
    yield


app = FastAPI(
    title="eve-price-compare API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(watchlist_router)
app.include_router(market_router)
app.include_router(reactions_router)
