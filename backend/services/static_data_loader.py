import csv
import os
from collections.abc import Iterable
from pathlib import Path

from sqlalchemy import func, select

from ..database import SessionLocal
from ..models import EveType, MarketPrice, ReactionInput, ReactionRecipe


MOCK_EVE_TYPES = [
    {
        "type_id": 34,
        "name": "Tritanium",
        "group_id": 18,
        "market_group_id": 1857,
        "published": True,
    },
    {
        "type_id": 35,
        "name": "Pyerite",
        "group_id": 18,
        "market_group_id": 1857,
        "published": True,
    },
    {
        "type_id": 36,
        "name": "Mexallon",
        "group_id": 18,
        "market_group_id": 1857,
        "published": True,
    },
    {
        "type_id": 37,
        "name": "Isogen",
        "group_id": 18,
        "market_group_id": 1857,
        "published": True,
    },
    {
        "type_id": 38,
        "name": "Nocxium",
        "group_id": 18,
        "market_group_id": 1857,
        "published": True,
    },
    {
        "type_id": 39,
        "name": "Zydrine",
        "group_id": 18,
        "market_group_id": 1857,
        "published": True,
    },
    {
        "type_id": 40,
        "name": "Megacyte",
        "group_id": 18,
        "market_group_id": 1857,
        "published": True,
    },
    {
        "type_id": 44992,
        "name": "PLEX",
        "group_id": 1874,
        "market_group_id": 2456,
        "published": True,
    },
    {
        "type_id": 587,
        "name": "Rifter",
        "group_id": 25,
        "market_group_id": 64,
        "published": True,
    },
    {
        "type_id": 603,
        "name": "Merlin",
        "group_id": 25,
        "market_group_id": 64,
        "published": True,
    },
    {
        "type_id": 16633,
        "name": "Hydrocarbons",
        "group_id": 427,
        "market_group_id": 1332,
        "published": True,
    },
    {
        "type_id": 16634,
        "name": "Atmospheric Gases",
        "group_id": 427,
        "market_group_id": 1332,
        "published": True,
    },
    {
        "type_id": 16641,
        "name": "Evaporite Deposits",
        "group_id": 427,
        "market_group_id": 1332,
        "published": True,
    },
    {
        "type_id": 16643,
        "name": "Cadmium",
        "group_id": 427,
        "market_group_id": 1332,
        "published": True,
    },
    {
        "type_id": 17959,
        "name": "Cadmium Hafnite Reaction Formula",
        "group_id": 1888,
        "market_group_id": 2767,
        "published": True,
    },
    {
        "type_id": 16659,
        "name": "Cadmium Hafnite",
        "group_id": 428,
        "market_group_id": 1334,
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
    def __init__(self, csv_path: str | None = None) -> None:
        self.csv_path = csv_path or os.getenv("EVE_TYPES_CSV_PATH")
        self.reaction_products_csv_path = os.getenv("EVE_REACTION_PRODUCTS_CSV_PATH")
        self.reaction_materials_csv_path = os.getenv("EVE_REACTION_MATERIALS_CSV_PATH")
        self.reaction_activities_csv_path = os.getenv("EVE_REACTION_ACTIVITIES_CSV_PATH")

    def load(self) -> int:
        with SessionLocal() as db:
            loaded_count = 0
            existing_count = db.scalar(select(func.count(EveType.type_id))) or 0
            if existing_count == 0:
                rows = list(self._load_rows())
                db.bulk_save_objects([EveType(**row) for row in rows])
                loaded_count += len(rows)
            else:
                for row in MOCK_EVE_TYPES:
                    if db.get(EveType, row["type_id"]) is None:
                        db.add(EveType(**row))
                        loaded_count += 1

            loaded_count += self._load_reaction_rows(db)
            loaded_count += self._load_mock_prices(db)
            db.commit()
            return loaded_count

    def _load_rows(self) -> Iterable[dict]:
        if self.csv_path:
            path = Path(self.csv_path)
            if path.exists():
                return self._load_fuzzwork_inv_types(path)

        return MOCK_EVE_TYPES

    def _load_fuzzwork_inv_types(self, path: Path) -> list[dict]:
        rows: list[dict] = []
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                parsed = self._parse_fuzzwork_row(row)
                if parsed is not None:
                    rows.append(parsed)
        return rows

    def _load_reaction_rows(self, db) -> int:
        existing_count = db.scalar(select(func.count(ReactionRecipe.id))) or 0
        if existing_count > 0:
            return 0

        recipes, inputs = self._load_reaction_source_rows()
        db.bulk_save_objects([ReactionRecipe(**row) for row in recipes])
        db.bulk_save_objects([ReactionInput(**row) for row in inputs])
        return len(recipes) + len(inputs)

    def _load_reaction_source_rows(self) -> tuple[list[dict], list[dict]]:
        products_path = _existing_path(self.reaction_products_csv_path)
        materials_path = _existing_path(self.reaction_materials_csv_path)
        activities_path = _existing_path(self.reaction_activities_csv_path)

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

    @staticmethod
    def _parse_fuzzwork_row(row: dict[str, str]) -> dict | None:
        type_id = _parse_int(row.get("typeID"))
        name = row.get("typeName")
        published = _parse_bool(row.get("published"))
        market_group_id = _parse_int(row.get("marketGroupID"))

        if type_id is None or not name or not published or market_group_id is None:
            return None

        return {
            "type_id": type_id,
            "name": name,
            "group_id": _parse_int(row.get("groupID")),
            "market_group_id": market_group_id,
            "published": published,
        }


def _parse_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.lower() in {"1", "true", "t", "yes"}


def _existing_path(value: str | None) -> Path | None:
    if value is None or value == "":
        return None

    path = Path(value)
    return path if path.exists() else None
