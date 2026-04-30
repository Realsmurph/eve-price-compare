import csv
import os
from collections.abc import Iterable
from pathlib import Path

import httpx
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from ..config import SDE_BASE_URL, SDE_CACHE_DIR
from ..database import SessionLocal
from ..models import EveType, MarketPrice, ReactionInput, ReactionRecipe


UPSERT_BATCH_SIZE = 1000


MOCK_EVE_TYPES = [
    {
        "type_id": 34,
        "name": "Tritanium",
        "group_id": 18,
        "group_name": "Mineral",
        "category_id": 4,
        "category_name": "Material",
        "market_group_id": 1857,
        "volume": "0.01",
        "published": True,
    },
    {
        "type_id": 35,
        "name": "Pyerite",
        "group_id": 18,
        "group_name": "Mineral",
        "category_id": 4,
        "category_name": "Material",
        "market_group_id": 1857,
        "volume": "0.01",
        "published": True,
    },
    {
        "type_id": 36,
        "name": "Mexallon",
        "group_id": 18,
        "group_name": "Mineral",
        "category_id": 4,
        "category_name": "Material",
        "market_group_id": 1857,
        "volume": "0.01",
        "published": True,
    },
    {
        "type_id": 37,
        "name": "Isogen",
        "group_id": 18,
        "group_name": "Mineral",
        "category_id": 4,
        "category_name": "Material",
        "market_group_id": 1857,
        "volume": "0.01",
        "published": True,
    },
    {
        "type_id": 38,
        "name": "Nocxium",
        "group_id": 18,
        "group_name": "Mineral",
        "category_id": 4,
        "category_name": "Material",
        "market_group_id": 1857,
        "volume": "0.01",
        "published": True,
    },
    {
        "type_id": 39,
        "name": "Zydrine",
        "group_id": 18,
        "group_name": "Mineral",
        "category_id": 4,
        "category_name": "Material",
        "market_group_id": 1857,
        "volume": "0.01",
        "published": True,
    },
    {
        "type_id": 40,
        "name": "Megacyte",
        "group_id": 18,
        "group_name": "Mineral",
        "category_id": 4,
        "category_name": "Material",
        "market_group_id": 1857,
        "volume": "0.01",
        "published": True,
    },
    {
        "type_id": 44992,
        "name": "PLEX",
        "group_id": 1874,
        "group_name": "PLEX",
        "category_id": 63,
        "category_name": "Special Edition Assets",
        "market_group_id": 2456,
        "volume": "0.01",
        "published": True,
    },
    {
        "type_id": 587,
        "name": "Rifter",
        "group_id": 25,
        "group_name": "Frigate",
        "category_id": 6,
        "category_name": "Ship",
        "market_group_id": 64,
        "volume": "27289.0",
        "published": True,
    },
    {
        "type_id": 603,
        "name": "Merlin",
        "group_id": 25,
        "group_name": "Frigate",
        "category_id": 6,
        "category_name": "Ship",
        "market_group_id": 64,
        "volume": "16500.0",
        "published": True,
    },
    {
        "type_id": 16633,
        "name": "Hydrocarbons",
        "group_id": 427,
        "group_name": "Moon Materials",
        "category_id": 4,
        "category_name": "Material",
        "market_group_id": 1332,
        "volume": "1.0",
        "published": True,
    },
    {
        "type_id": 16634,
        "name": "Atmospheric Gases",
        "group_id": 427,
        "group_name": "Moon Materials",
        "category_id": 4,
        "category_name": "Material",
        "market_group_id": 1332,
        "volume": "1.0",
        "published": True,
    },
    {
        "type_id": 16641,
        "name": "Evaporite Deposits",
        "group_id": 427,
        "group_name": "Moon Materials",
        "category_id": 4,
        "category_name": "Material",
        "market_group_id": 1332,
        "volume": "1.0",
        "published": True,
    },
    {
        "type_id": 16643,
        "name": "Cadmium",
        "group_id": 427,
        "group_name": "Moon Materials",
        "category_id": 4,
        "category_name": "Material",
        "market_group_id": 1332,
        "volume": "1.0",
        "published": True,
    },
    {
        "type_id": 17959,
        "name": "Cadmium Hafnite Reaction Formula",
        "group_id": 1888,
        "group_name": "Reaction Formulas",
        "category_id": 9,
        "category_name": "Blueprint",
        "market_group_id": 2767,
        "volume": "0.01",
        "published": True,
    },
    {
        "type_id": 16659,
        "name": "Cadmium Hafnite",
        "group_id": 428,
        "group_name": "Intermediate Materials",
        "category_id": 4,
        "category_name": "Material",
        "market_group_id": 1334,
        "volume": "1.0",
        "published": True,
    },
]

MOCK_REACTION_RECIPES = [
    {
        "reaction_type_id": 17959,
        "output_type_id": 16659,
        "output_quantity": 200,
        "duration_seconds": 3600,
        "activity_id": 11,
    },
]

MOCK_REACTION_INPUTS = [
    {
        "reaction_type_id": 17959,
        "input_type_id": 16633,
        "quantity": 100,
        "activity_id": 11,
    },
    {
        "reaction_type_id": 17959,
        "input_type_id": 16634,
        "quantity": 100,
        "activity_id": 11,
    },
    {
        "reaction_type_id": 17959,
        "input_type_id": 16641,
        "quantity": 100,
        "activity_id": 11,
    },
    {
        "reaction_type_id": 17959,
        "input_type_id": 16643,
        "quantity": 100,
        "activity_id": 11,
    },
]

MOCK_MARKET_PRICES = [
    {"type_id": 16633, "buy": "580.00", "sell": "600.00"},
    {"type_id": 16634, "buy": "380.00", "sell": "400.00"},
    {"type_id": 16641, "buy": "280.00", "sell": "300.00"},
    {"type_id": 16643, "buy": "1780.00", "sell": "1800.00"},
    {"type_id": 16659, "buy": "1950.00", "sell": "2100.00"},
]


class StaticDataLoader:
    def __init__(self, csv_path: str | None = None, sde_base_url: str | None = None) -> None:
        self.csv_path = csv_path or os.getenv("EVE_TYPES_CSV_PATH")
        self.reaction_products_csv_path = os.getenv("EVE_REACTION_PRODUCTS_CSV_PATH")
        self.reaction_materials_csv_path = os.getenv("EVE_REACTION_MATERIALS_CSV_PATH")
        self.reaction_activities_csv_path = os.getenv("EVE_REACTION_ACTIVITIES_CSV_PATH")
        self.group_csv_path = os.getenv("EVE_GROUPS_CSV_PATH")
        self.category_csv_path = os.getenv("EVE_CATEGORIES_CSV_PATH")
        self.sde_base_url = (sde_base_url or SDE_BASE_URL).rstrip("/")
        self.cache_dir = Path(os.getenv("SDE_CACHE_DIR", SDE_CACHE_DIR))

    def load(self, force: bool = False) -> int:
        with SessionLocal() as db:
            loaded_count = 0
            existing_count = db.scalar(select(func.count(EveType.type_id))) or 0
            missing_metadata_count = (
                db.scalar(
                    select(func.count(EveType.type_id)).where(EveType.category_name.is_(None))
                )
                or 0
            )
            if existing_count == 0 or missing_metadata_count > 0 or force:
                rows = list(self._load_rows())
                self._upsert_eve_types(db, rows)
                loaded_count += len(rows)
            else:
                for row in MOCK_EVE_TYPES:
                    if db.get(EveType, row["type_id"]) is None:
                        db.add(EveType(**row))
                        loaded_count += 1

            loaded_count += self._load_reaction_rows(db, force=force)
            loaded_count += self._load_mock_prices(db)
            db.commit()
            return loaded_count

    def _load_rows(self) -> Iterable[dict]:
        paths = self._resolve_sde_paths()
        types_path = paths.get("invTypes")
        if types_path:
            return self._load_fuzzwork_inv_types(
                types_path,
                paths.get("invGroups"),
                paths.get("invCategories"),
            )

        return MOCK_EVE_TYPES

    def _load_fuzzwork_inv_types(
        self,
        path: Path,
        groups_path: Path | None = None,
        categories_path: Path | None = None,
    ) -> list[dict]:
        groups = self._load_groups(groups_path)
        categories = self._load_categories(categories_path)
        rows: list[dict] = []
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                parsed = self._parse_fuzzwork_row(row, groups, categories)
                if parsed is not None:
                    rows.append(parsed)
        return rows

    def _load_reaction_rows(self, db, force: bool = False) -> int:
        existing_count = db.scalar(select(func.count(ReactionRecipe.id))) or 0
        if existing_count > 0 and not force:
            return 0

        recipes, inputs = self._load_reaction_source_rows()
        if force:
            db.query(ReactionInput).delete()
            db.query(ReactionRecipe).delete()
        if recipes:
            db.bulk_save_objects([ReactionRecipe(**row) for row in recipes])
        if inputs:
            db.bulk_save_objects([ReactionInput(**row) for row in inputs])
        return len(recipes) + len(inputs)

    def _load_reaction_source_rows(self) -> tuple[list[dict], list[dict]]:
        paths = self._resolve_sde_paths()
        products_path = _existing_path(self.reaction_products_csv_path) or paths.get(
            "industryActivityProducts"
        )
        materials_path = _existing_path(self.reaction_materials_csv_path) or paths.get(
            "industryActivityMaterials"
        )
        activities_path = _existing_path(self.reaction_activities_csv_path) or paths.get(
            "industryActivity"
        )

        if products_path and materials_path and activities_path:
            return self._load_fuzzwork_reactions(
                products_path,
                materials_path,
                activities_path,
            )

        return MOCK_REACTION_RECIPES, MOCK_REACTION_INPUTS

    def _load_fuzzwork_reactions(
        self,
        products_path: Path,
        materials_path: Path,
        activities_path: Path,
    ) -> tuple[list[dict], list[dict]]:
        durations = self._load_reaction_durations(activities_path)
        recipes: list[dict] = []
        inputs: list[dict] = []

        with products_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                activity_id = _parse_int(row.get("activityID"))
                reaction_type_id = _parse_int(row.get("typeID"))
                output_type_id = _parse_int(row.get("productTypeID"))
                quantity = _parse_int(row.get("quantity"))
                if (
                    activity_id != 11
                    or reaction_type_id is None
                    or output_type_id is None
                    or quantity is None
                ):
                    continue

                recipes.append(
                    {
                        "reaction_type_id": reaction_type_id,
                        "output_type_id": output_type_id,
                        "output_quantity": quantity,
                        "duration_seconds": durations.get(reaction_type_id, 3600),
                        "activity_id": 11,
                    }
                )

        with materials_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                activity_id = _parse_int(row.get("activityID"))
                reaction_type_id = _parse_int(row.get("typeID"))
                input_type_id = _parse_int(row.get("materialTypeID"))
                quantity = _parse_int(row.get("quantity"))
                if (
                    activity_id != 11
                    or reaction_type_id is None
                    or input_type_id is None
                    or quantity is None
                ):
                    continue

                inputs.append(
                    {
                        "reaction_type_id": reaction_type_id,
                        "input_type_id": input_type_id,
                        "quantity": quantity,
                        "activity_id": 11,
                    }
                )

        return recipes, inputs

    def _load_reaction_durations(self, activities_path: Path) -> dict[int, int]:
        durations: dict[int, int] = {}
        with activities_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                activity_id = _parse_int(row.get("activityID"))
                reaction_type_id = _parse_int(row.get("typeID"))
                duration = _parse_int(row.get("time"))
                if activity_id == 11 and reaction_type_id is not None and duration is not None:
                    durations[reaction_type_id] = duration
        return durations

    def _load_mock_prices(self, db) -> int:
        loaded_count = 0
        for row in MOCK_MARKET_PRICES:
            if db.get(MarketPrice, row["type_id"]) is None:
                db.add(MarketPrice(**row))
                loaded_count += 1
        return loaded_count

    def _resolve_sde_paths(self) -> dict[str, Path]:
        local_paths = {
            "invTypes": _existing_path(self.csv_path),
            "invGroups": _existing_path(self.group_csv_path),
            "invCategories": _existing_path(self.category_csv_path),
            "industryActivityProducts": _existing_path(self.reaction_products_csv_path),
            "industryActivityMaterials": _existing_path(self.reaction_materials_csv_path),
            "industryActivity": _existing_path(self.reaction_activities_csv_path),
        }
        if local_paths["invTypes"]:
            return {key: path for key, path in local_paths.items() if path}

        names = [
            "invTypes",
            "invGroups",
            "invCategories",
            "industryActivityProducts",
            "industryActivityMaterials",
            "industryActivity",
        ]
        return {
            name: path
            for name in names
            if (path := self._download_sde_csv(name)) is not None
        }

    def _download_sde_csv(self, name: str) -> Path | None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / f"{name}.csv"
        if path.exists() and path.stat().st_size > 0:
            return path

        url = f"{self.sde_base_url}/{name}.csv"
        try:
            with httpx.stream("GET", url, timeout=60.0, follow_redirects=True) as response:
                response.raise_for_status()
                with path.open("wb") as handle:
                    for chunk in response.iter_bytes():
                        handle.write(chunk)
        except httpx.HTTPError:
            if path.exists():
                path.unlink()
            return None
        return path

    def _upsert_eve_types(self, db, rows: list[dict]) -> None:
        for batch_start in range(0, len(rows), UPSERT_BATCH_SIZE):
            batch = rows[batch_start : batch_start + UPSERT_BATCH_SIZE]
            if not batch:
                continue
            statement = insert(EveType).values(batch)
            update_columns = {
                column.name: getattr(statement.excluded, column.name)
                for column in EveType.__table__.columns
                if column.name != "type_id"
            }
            db.execute(
                statement.on_conflict_do_update(
                    index_elements=["type_id"],
                    set_=update_columns,
                )
            )

    def _load_groups(self, path: Path | None) -> dict[int, dict]:
        if path is None:
            return {}

        groups: dict[int, dict] = {}
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                group_id = _parse_int(row.get("groupID"))
                if group_id is None:
                    continue
                groups[group_id] = {
                    "group_name": row.get("groupName") or None,
                    "category_id": _parse_int(row.get("categoryID")),
                }
        return groups

    def _load_categories(self, path: Path | None) -> dict[int, str]:
        if path is None:
            return {}

        categories: dict[int, str] = {}
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                category_id = _parse_int(row.get("categoryID"))
                category_name = row.get("categoryName")
                if category_id is not None and category_name:
                    categories[category_id] = category_name
        return categories

    @staticmethod
    def _parse_fuzzwork_row(
        row: dict[str, str],
        groups: dict[int, dict] | None = None,
        categories: dict[int, str] | None = None,
    ) -> dict | None:
        type_id = _parse_int(row.get("typeID"))
        name = row.get("typeName")
        published = _parse_bool(row.get("published"))
        market_group_id = _parse_int(row.get("marketGroupID"))

        if type_id is None or not name or not published or market_group_id is None:
            return None

        group_id = _parse_int(row.get("groupID"))
        group = (groups or {}).get(group_id or -1, {})
        category_id = group.get("category_id")
        return {
            "type_id": type_id,
            "name": name,
            "group_id": group_id,
            "group_name": group.get("group_name"),
            "category_id": category_id,
            "category_name": (categories or {}).get(category_id) if category_id is not None else None,
            "market_group_id": market_group_id,
            "volume": _parse_decimal(row.get("volume")),
            "published": published,
        }


def _parse_int(value: str | None) -> int | None:
    if value is None or value.strip().lower() in {"", "none", "null", "\\n"}:
        return None
    return int(value)


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.lower() in {"1", "true", "t", "yes"}


def _parse_decimal(value: str | None) -> str | None:
    if value is None or value.strip().lower() in {"", "none", "null", "\\n"}:
        return None
    return value


def _existing_path(value: str | None) -> Path | None:
    if value is None or value == "":
        return None

    path = Path(value)
    return path if path.exists() else None
