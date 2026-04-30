import os
import re
from decimal import Decimal
from html.parser import HTMLParser
from typing import TYPE_CHECKING

import httpx

from ..config import GOONMETRICS_BASE_URL, GOONMETRICS_CJ_STRUCTURE_ID
from ..schemas import MarketPricePair
from ..services.cache import TTLCache

if TYPE_CHECKING:
    from ..models import EveType


_PRICE_CACHE: TTLCache[MarketPricePair] = TTLCache(ttl_seconds=300, max_items=1024)


class GoonmetricsClient:
    """Reads C-J6MT prices from Goonmetrics import pages, with env overrides for private setups."""

    def __init__(
        self,
        base_url: str = GOONMETRICS_BASE_URL,
        structure_id: str = GOONMETRICS_CJ_STRUCTURE_ID,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.structure_id = structure_id
        self.timeout_seconds = timeout_seconds

    async def get_cj_prices(self, eve_type: "EveType | None") -> MarketPricePair:
        env_prices = self._read_env_prices()
        if env_prices.buy is not None or env_prices.sell is not None:
            return env_prices

        if eve_type is None or eve_type.market_group_id is None:
            return MarketPricePair()

        cache_key = f"cj:{eve_type.type_id}:{eve_type.market_group_id}"
        cached_prices = _PRICE_CACHE.get(cache_key)
        if cached_prices is not None:
            return cached_prices

        buy = await self._fetch_price(eve_type, from_price="buy")
        sell = await self._fetch_price(eve_type, from_price="sell")
        prices = MarketPricePair(buy=buy, sell=sell)
        _PRICE_CACHE.set(cache_key, prices)
        return prices

    async def _fetch_price(self, eve_type: "EveType", from_price: str) -> Decimal | None:
        url = (
            f"{self.base_url}/importing/{self.structure_id}/"
            f"marketgroup/{eve_type.market_group_id}/"
        )
        params = {"from": from_price}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
        except httpx.HTTPError:
            return None

        rows = _GoonmetricsTableParser.parse(response.text)
        for row in rows:
            if not row or row[0].strip().lower() != eve_type.name.strip().lower():
                continue
            if len(row) < 6:
                return None
            return _parse_price(row[5])
        return None

    def _read_env_prices(self) -> MarketPricePair:
        return MarketPricePair(
            buy=self._read_price("GOONMETRICS_STUB_BUY"),
            sell=self._read_price("GOONMETRICS_STUB_SELL"),
        )

    @staticmethod
    def _read_price(env_name: str) -> Decimal | None:
        raw_value = os.getenv(env_name)
        if raw_value is None or raw_value == "":
            return None
        return Decimal(raw_value)


class _GoonmetricsTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None

    @classmethod
    def parse(cls, html: str) -> list[list[str]]:
        parser = cls()
        parser.feed(html)
        return parser.rows

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "tr":
            self._current_row = []
        elif tag in {"td", "th"} and self._current_row is not None:
            self._current_cell = []

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._current_row is not None and self._current_cell is not None:
            self._current_row.append(" ".join(part.strip() for part in self._current_cell).strip())
            self._current_cell = None
        elif tag == "tr" and self._current_row is not None:
            if self._current_row:
                self.rows.append(self._current_row)
            self._current_row = None


def _parse_price(value: str) -> Decimal | None:
    normalized = re.sub(r"[^0-9.]", "", value)
    if not normalized:
        return None
    return Decimal(normalized)
