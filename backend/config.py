import os
from decimal import Decimal


def _csv_env(name: str, default: str = "") -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


APP_ENV = os.getenv("APP_ENV", "production")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/eve_price_compare",
)
CORS_ORIGINS = _csv_env(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
RUN_STATIC_DATA_LOADER = os.getenv("RUN_STATIC_DATA_LOADER", "true").lower() in {
    "1",
    "true",
    "yes",
}
SDE_BASE_URL = os.getenv("SDE_BASE_URL", "https://www.fuzzwork.co.uk/dump/latest")
SDE_CACHE_DIR = os.getenv("SDE_CACHE_DIR", "/app/data/sde-cache")
GOONMETRICS_BASE_URL = os.getenv(
    "GOONMETRICS_BASE_URL",
    "https://goonmetrics.apps.goonswarm.org",
)
GOONMETRICS_CJ_STRUCTURE_ID = os.getenv("GOONMETRICS_CJ_STRUCTURE_ID", "1049588174021")
ITL_SHIPPING_PROVIDER = os.getenv(
    "ITL_SHIPPING_PROVIDER",
    "Imperial Transcontinental Logistics",
)
ITL_SHIPPING_ROUTE = os.getenv("ITL_SHIPPING_ROUTE", "Jita 4-4 -> C-J6MT")
ITL_SHIPPING_RATE_PER_M3 = Decimal(os.getenv("ITL_SHIPPING_RATE_PER_M3", "800"))
ITL_SHIPPING_MIN_FEE = Decimal(os.getenv("ITL_SHIPPING_MIN_FEE", "0"))
