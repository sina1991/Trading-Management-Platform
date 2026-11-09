"""Provider-neutral contract for public market-data adapters."""
from typing import Protocol

from trading_platform.markets.market_data import MarketQuote, OrderBookSnapshot


class MarketDataProvider(Protocol):
    provider_name: str

    def get_order_book(self, product_id: str, limit: int = 20) -> OrderBookSnapshot:
        """Fetch a public order-book snapshot; must never place an order."""

    def get_quote(self, product_id: str) -> MarketQuote:
        """Fetch and normalize the current best bid and ask."""
