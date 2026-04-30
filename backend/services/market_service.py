from decimal import Decimal

from ..clients.esi import ESIClient, decimal_from_esi_price
from ..clients.goonmetrics import GoonmetricsClient
from ..schemas import MarketComparisonRead, MarketPricePair
from .cache import TTLCache


THE_FORGE_REGION_ID = 10000002
DOMAIN_REGION_ID = 10000043
_COMPARISON_CACHE: TTLCache[MarketComparisonRead] = TTLCache(ttl_seconds=300, max_items=1024)


class MarketService:
    def __init__(
        self,
        esi_client: ESIClient | None = None,
        goonmetrics_client: GoonmetricsClient | None = None,
    ) -> None:
        self.esi_client = esi_client or ESIClient()
        self.goonmetrics_client = goonmetrics_client or GoonmetricsClient()

    async def compare_item(self, type_id: int) -> MarketComparisonRead:
        cache_key = f"compare:{type_id}"
        cached_comparison = _COMPARISON_CACHE.get(cache_key)
        if cached_comparison is not None:
            return cached_comparison

        jita_orders = await self.esi_client.get_region_orders(THE_FORGE_REGION_ID, type_id)
        amarr_orders = await self.esi_client.get_region_orders(DOMAIN_REGION_ID, type_id)

        comparison = MarketComparisonRead(
            jita=self._aggregate_orders(jita_orders),
            amarr=self._aggregate_orders(amarr_orders),
            cj=self.goonmetrics_client.get_cj_prices(type_id),
        )
        _COMPARISON_CACHE.set(cache_key, comparison)
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
