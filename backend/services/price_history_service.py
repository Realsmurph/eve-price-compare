from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import MarketPriceHistory
from ..schemas import MarketComparisonRead, MarketPricePair


class PriceHistoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record_comparison(
        self,
        type_id: int,
        comparison: MarketComparisonRead,
        source: str = "snapshot",
        history_date: date | None = None,
    ) -> int:
        rows = [
            self._build_row(type_id, "jita", comparison.jita, source, history_date),
            self._build_row(type_id, "amarr", comparison.amarr, source, history_date),
            self._build_row(type_id, "cj", comparison.cj, source, history_date),
        ]
        self.db.add_all(rows)
        self.db.commit()
        return len(rows)

    def list_history(
        self,
        type_id: int,
        hub: str | None = None,
        limit: int = 90,
    ) -> list[MarketPriceHistory]:
        statement = select(MarketPriceHistory).where(MarketPriceHistory.type_id == type_id)
        if hub:
            statement = statement.where(MarketPriceHistory.hub == hub.lower())

        statement = statement.order_by(MarketPriceHistory.observed_at.desc()).limit(limit)
        return list(self.db.scalars(statement))

    @staticmethod
    def _build_row(
        type_id: int,
        hub: str,
        prices: MarketPricePair,
        source: str,
        history_date: date | None,
    ) -> MarketPriceHistory:
        return MarketPriceHistory(
            type_id=type_id,
            hub=hub,
            buy=Decimal(prices.buy) if prices.buy is not None else None,
            sell=Decimal(prices.sell) if prices.sell is not None else None,
            source=source,
            history_date=history_date,
        )
