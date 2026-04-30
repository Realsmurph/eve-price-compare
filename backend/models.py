from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_type_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class EveType(Base):
    __tablename__ = "eve_types"

    type_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    group_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    market_group_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ReactionRecipe(Base):
    __tablename__ = "reaction_recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reaction_type_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    output_type_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    output_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    activity_id: Mapped[int] = mapped_column(Integer, default=11, nullable=False)


class ReactionInput(Base):
    __tablename__ = "reaction_inputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reaction_type_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    input_type_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    activity_id: Mapped[int] = mapped_column(Integer, default=11, nullable=False)


class MarketPrice(Base):
    __tablename__ = "market_prices"

    type_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    buy: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    sell: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
