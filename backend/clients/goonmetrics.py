import os
from decimal import Decimal

from ..schemas import MarketPricePair


class GoonmetricsClient:
    """Stubbed CJ market client with optional env-backed mock prices."""

    def get_cj_prices(self, type_id: int) -> MarketPricePair:
        buy = self._read_price("GOONMETRICS_STUB_BUY")
        sell = self._read_price("GOONMETRICS_STUB_SELL")
        return MarketPricePair(buy=buy, sell=sell)

    @staticmethod
    def _read_price(env_name: str) -> Decimal | None:
        raw_value = os.getenv(env_name)
        if raw_value is None or raw_value == "":
            return None
        return Decimal(raw_value)
