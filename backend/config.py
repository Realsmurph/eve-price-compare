import os


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
