from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..clients.esi import ESIClient
from ..models import EveType, MarketPriceHistory, WatchlistItem
from .market_service import DOMAIN_REGION_ID, THE_FORGE_REGION_ID, MarketService


class PriceRefreshService:
    def __init__(self, db: Session, esi_client: ESIClient | None = None) -> None:
        self.db = db
        self.esi_client = esi_client or ESIClient()

    async def refresh_snapshots(self, limit: int = 250, all_items: bool = False) -> int:
        type_ids = self._type_ids(limit=limit, all_items=all_items)
        service = MarketService(self.db, esi_client=self.esi_client)
        count = 0
        for type_id in type_ids:
            await service.compare_item(type_id, record_history=True)
            count += 1
        return count

    async def refresh_daily_history(self, limit: int = 250, all_items: bool = False) -> int:
        type_ids = self._type_ids(limit=limit, all_items=all_items)
        inserted = 0
        for type_id in type_ids:
            inserted += await self._load_esi_history(type_id, "jita", THE_FORGE_REGION_ID)
            inserted += await self._load_esi_history(type_id, "amarr", DOMAIN_REGION_ID)
        self.db.commit()
        return inserted

    def _type_ids(self, limit: int, all_items: bool) -> list[int]:
        if all_items:
            statement = (
                select(EveType.type_id)
                .where(EveType.published.is_(True))
                .where(EveType.market_group_id.is_not(None))
                .order_by(EveType.type_id.asc())
                .limit(limit)
            )
            return list(self.db.scalars(statement))

        watchlist_ids = list(self.db.scalars(select(WatchlistItem.item_type_id)))
        if watchlist_ids:
            return sorted(set(watchlist_ids))[:limit]

        statement = (
            select(EveType.type_id)
            .where(EveType.published.is_(True))
            .where(EveType.market_group_id.is_not(None))
            .order_by(EveType.name.asc())
            .limit(limit)
        )
        return list(self.db.scalars(statement))

    async def _load_esi_history(self, type_id: int, hub: str, region_id: int) -> int:
        rows = await self.esi_client.get_market_history(region_id, type_id)
        inserted = 0
        for row in rows:
            raw_history_date = row.get("date")
            if not raw_history_date:
                continue
            history_date = date.fromisoformat(raw_history_date)
            exists_statement = (
                select(MarketPriceHistory.id)
                .where(MarketPriceHistory.type_id == type_id)
                .where(MarketPriceHistory.hub == hub)
                .where(MarketPriceHistory.source == "esi-history")
                .where(MarketPriceHistory.history_date == history_date)
            )
            if self.db.scalar(exists_statement) is not None:
                continue
            self.db.add(
                MarketPriceHistory(
                    type_id=type_id,
                    hub=hub,
                    buy=None,
                    sell=Decimal(str(row["average"])) if row.get("average") is not None else None,
                    source="esi-history",
                    history_date=history_date,
                )
            )
            inserted += 1
        return inserted
