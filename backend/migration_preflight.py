from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from .database import engine


def main() -> None:
    config = Config("alembic.ini")
    with engine.connect() as connection:
        inspector = inspect(connection)
        table_names = set(inspector.get_table_names())

    expected_tables = {
        "eve_types",
        "market_prices",
        "reaction_inputs",
        "reaction_recipes",
        "watchlist_items",
    }
    has_app_tables = expected_tables.issubset(table_names)
    has_alembic_version = "alembic_version" in table_names

    if has_app_tables and not has_alembic_version:
        command.stamp(config, "20260430_0001")


if __name__ == "__main__":
    main()
