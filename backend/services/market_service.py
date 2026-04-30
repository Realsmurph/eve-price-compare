from decimal import Decimal

from sqlalchemy.orm import Session

from ..clients.esi import ESIClient, decimal_from_esi_price
from ..clients.goonmetrics import GoonmetricsClient
from ..models import EveType
from ..schemas import MarketComparisonRead, MarketPricePair
from .cache import TTLCache
from .price_history_service import PriceHistoryService


THE_FORGE_REGION_ID = 10000002
DOMAIN_REGION_ID = 10000043
_COMPARISON_CACHE: TTLCache[MarketComparisonRead] = TTLCache(ttl_seconds=300, max_items=1024)


class MarketService:
    def __init__(
        self,
        db: Session,
        esi_client: ESIClient | None = None,
        goonmetrics_client: GoonmetricsClient | None = None,
    ) -> None:
        self.db = db
        self.esi_client = esi_client or ESIClient()
        self.goonmetrics_client = goonmetrics_client or GoonmetricsClient()

    async def compare_item(self, type_id: int, record_history: bool = True) -> MarketComparisonRead:
        cache_key = f"compare:{type_id}"
        cached_comparison = _COMPARISON_CACHE.get(cache_key)
        if cached_comparison is not None:
            if record_history:
                PriceHistoryService(self.db).record_comparison(type_id, cached_comparison, source="cache")
            return cached_comparison

        eve_type = self.db.get(EveType, type_id)
        jita_orders = await self.esi_client.get_region_orders(THE_FORGE_REGION_ID, type_id)
        amarr_orders = await self.esi_client.get_region_orders(DOMAIN_REGION_ID, type_id)

        comparison = MarketComparisonRead(
            jita=self._aggregate_orders(jita_orders),
            amarr=self._aggregate_orders(amarr_orders),
            cj=await self.goonmetrics_client.get_cj_prices(eve_type),
        )
        _COMPARISON_CACHE.set(cache_key, comparison)
        if record_history:
            PriceHistoryService(self.db).record_comparison(type_id, comparison)
        return comparison

    @staticmethod
    def _aggregate_orders(orders: list[dict]) -> MarketPricePair:
        buy_prices: list[Decimal] = []
        sell_prices: list[Decimal] = []

        for order in orders:
            if "price" not in order:
                continue

            price = decimal_from_esi_price(order["price"])
            if order.get("is_buy_order", False):
                buy_prices.append(price)
            else:
                sell_prices.append(price)

        return MarketPricePair(
            buy=max(buy_prices) if buy_prices else None,
            sell=min(sell_prices) if sell_prices else None,
        )
