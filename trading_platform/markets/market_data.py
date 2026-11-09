"""Provider-neutral, read-only market-data value objects."""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional


class MarketDataError(RuntimeError):
    """Base error for market-data retrieval and validation."""


class MarketDataUnavailable(MarketDataError):
    """The provider could not return market data."""


class InvalidMarketData(MarketDataError):
    """The provider response was malformed or internally inconsistent."""


@dataclass(frozen=True)
class OrderBookLevel:
    price: Decimal
    size: Decimal

    def __post_init__(self) -> None:
        if not self.price.is_finite() or self.price <= 0:
            raise InvalidMarketData("Order-book price must be finite and positive")
        if not self.size.is_finite() or self.size <= 0:
            raise InvalidMarketData("Order-book size must be finite and positive")


@dataclass(frozen=True)
class OrderBookSnapshot:
    provider: str
    product_id: str
    bids: tuple[OrderBookLevel, ...]
    asks: tuple[OrderBookLevel, ...]
    received_at: datetime
    exchange_timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.provider or not self.product_id:
            raise InvalidMarketData("Provider and product ID are required")
        if not self.bids or not self.asks:
            raise InvalidMarketData("Both bid and ask sides must be present")
        if self.bids[0].price >= self.asks[0].price:
            raise InvalidMarketData("Order book is crossed or locked")

    @property
    def best_bid(self) -> OrderBookLevel:
        return self.bids[0]

    @property
    def best_ask(self) -> OrderBookLevel:
        return self.asks[0]

    @property
    def spread(self) -> Decimal:
        return self.best_ask.price - self.best_bid.price

    @property
    def midpoint(self) -> Decimal:
        return (self.best_ask.price + self.best_bid.price) / Decimal("2")

    @property
    def spread_bps(self) -> Decimal:
        return self.spread / self.midpoint * Decimal("10000")

    def age_seconds(self, now: Optional[datetime] = None) -> float:
        reference = now or datetime.now(timezone.utc)
        timestamp = self.exchange_timestamp or self.received_at
        if reference.tzinfo is None or timestamp.tzinfo is None:
            raise ValueError("Market-data timestamps must be timezone-aware")
        return max(0.0, (reference - timestamp).total_seconds())

    def is_stale(self, max_age_seconds: float = 10.0,
                 now: Optional[datetime] = None) -> bool:
        if max_age_seconds < 0:
            raise ValueError("max_age_seconds cannot be negative")
        return self.age_seconds(now) > max_age_seconds


@dataclass(frozen=True)
class MarketQuote:
    provider: str
    product_id: str
    bid: Decimal
    ask: Decimal
    bid_size: Decimal
    ask_size: Decimal
    midpoint: Decimal
    spread: Decimal
    spread_bps: Decimal
    received_at: datetime
    exchange_timestamp: Optional[datetime] = None

    @classmethod
    def from_order_book(cls, book: OrderBookSnapshot) -> "MarketQuote":
        return cls(
            provider=book.provider,
            product_id=book.product_id,
            bid=book.best_bid.price,
            ask=book.best_ask.price,
            bid_size=book.best_bid.size,
            ask_size=book.best_ask.size,
            midpoint=book.midpoint,
            spread=book.spread,
            spread_bps=book.spread_bps,
            received_at=book.received_at,
            exchange_timestamp=book.exchange_timestamp,
        )
