from decimal import Decimal
from typing import Any

import httpx

from ..services.cache import TTLCache


class ESIClientError(RuntimeError):
    pass


_ORDER_CACHE: TTLCache[list[dict[str, Any]]] = TTLCache(ttl_seconds=300, max_items=1024)
_HISTORY_CACHE: TTLCache[list[dict[str, Any]]] = TTLCache(ttl_seconds=3600, max_items=1024)


class ESIClient:
    def __init__(
        self,
        base_url: str = "https://esi.evetech.net/latest",
        datasource: str = "tranquility",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.datasource = datasource
        self.timeout_seconds = timeout_seconds

    async def get_region_orders(self, region_id: int, type_id: int) -> list[dict[str, Any]]:
        cache_key = f"{self.datasource}:{region_id}:{type_id}"
        cached_orders = _ORDER_CACHE.get(cache_key)
        if cached_orders is not None:
            return cached_orders

        orders: list[dict[str, Any]] = []
        page = 1
        pages = 1

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            while page <= pages:
                response = await client.get(
                    f"{self.base_url}/markets/{region_id}/orders/",
                    params={
                        "datasource": self.datasource,
                        "order_type": "all",
                        "page": page,
                        "type_id": type_id,
                    },
                )

                if response.status_code >= 400:
                    raise ESIClientError(
                        f"ESI market orders request failed with status {response.status_code}"
                    )

                orders.extend(response.json())
                pages = int(response.headers.get("X-Pages", "1"))
                page += 1

        _ORDER_CACHE.set(cache_key, orders)
        return orders

    async def get_market_history(self, region_id: int, type_id: int) -> list[dict[str, Any]]:
        cache_key = f"history:{self.datasource}:{region_id}:{type_id}"
        cached_history = _HISTORY_CACHE.get(cache_key)
        if cached_history is not None:
            return cached_history

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                f"{self.base_url}/markets/{region_id}/history/",
                params={
                    "datasource": self.datasource,
                    "type_id": type_id,
                },
            )

        if response.status_code >= 400:
            raise ESIClientError(
                f"ESI market history request failed with status {response.status_code}"
            )

        history = response.json()
        _HISTORY_CACHE.set(cache_key, history)
        return history


def decimal_from_esi_price(value: Any) -> Decimal:
    return Decimal(str(value))
