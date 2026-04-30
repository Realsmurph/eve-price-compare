from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class WatchlistItemBase(BaseModel):
    item_type_id: int = Field(gt=0)
    item_name: str = Field(min_length=1, max_length=255)
    target_price: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class WatchlistItemCreate(WatchlistItemBase):
    pass


class WatchlistItemUpdate(BaseModel):
    item_type_id: int | None = Field(default=None, gt=0)
    item_name: str | None = Field(default=None, min_length=1, max_length=255)
    target_price: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class WatchlistItemRead(WatchlistItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class MarketPricePair(BaseModel):
    buy: Decimal | None = None
    sell: Decimal | None = None

    @field_serializer("buy", "sell", when_used="json")
    def serialize_price(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class MarketComparisonRead(BaseModel):
    jita: MarketPricePair
    amarr: MarketPricePair
    cj: MarketPricePair


class EveTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type_id: int
    name: str
    group_id: int | None = None
    market_group_id: int | None = None
    published: bool


class ReactionLineItem(BaseModel):
    type_id: int
    name: str | None = None
    quantity: int
    unit_price: Decimal
    total: Decimal

    @field_serializer("unit_price", "total", when_used="json")
    def serialize_money(self, value: Decimal) -> float:
        return float(value)


class ReactionProfitRead(BaseModel):
    type_id: int
    reaction_type_id: int
    output_type_id: int
    output_name: str | None = None
    output_quantity: int
    duration_seconds: int
    input_cost: Decimal
    import_cost: Decimal
    total_cost: Decimal
    output_value: Decimal
    profit: Decimal
    profit_after_import: Decimal
    margin: Decimal | None
    margin_after_import: Decimal | None
    isk_per_hour: Decimal
    isk_per_hour_after_import: Decimal
    inputs: list[ReactionLineItem]

    @field_serializer(
        "input_cost",
        "import_cost",
        "total_cost",
        "output_value",
        "profit",
        "profit_after_import",
        "margin",
        "margin_after_import",
        "isk_per_hour",
        "isk_per_hour_after_import",
        when_used="json",
    )
    def serialize_metric(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None
