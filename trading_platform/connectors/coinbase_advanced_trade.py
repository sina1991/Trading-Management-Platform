"""Coinbase Advanced Trade public market-data adapter.

This adapter intentionally implements GET-only public endpoints. It has no
credential support and exposes no account, order, transfer, or execution API.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import re
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from trading_platform.connectors.market_data import MarketDataProvider
from trading_platform.markets.market_data import (
    InvalidMarketData,
    MarketDataUnavailable,
    MarketQuote,
    OrderBookLevel,
    OrderBookSnapshot,
)

BASE_URL = "https://api.coinbase.com/api/v3/brokerage/market"
_PRODUCT_ID = re.compile(r"^[A-Z0-9]{2,15}-[A-Z0-9]{2,15}$")


def _timestamp(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidMarketData("Provider timestamp must be a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidMarketData("Provider returned an invalid timestamp") from exc
    if parsed.tzinfo is None:
        raise InvalidMarketData("Provider timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _level(value: object) -> OrderBookLevel:
    if isinstance(value, dict):
        price, size = value.get("price"), value.get("size")
    elif isinstance(value, (list, tuple)) and len(value) >= 2:
        price, size = value[0], value[1]
    else:
        raise InvalidMarketData("Order-book level has an unsupported shape")
    try:
        return OrderBookLevel(Decimal(str(price)), Decimal(str(size)))
    except (InvalidOperation, TypeError, ValueError) as exc:
        if isinstance(exc, InvalidMarketData):
            raise
        raise InvalidMarketData("Order-book level contains an invalid number") from exc


class CoinbaseAdvancedTradeProvider(MarketDataProvider):
    """Read-only adapter for Coinbase's unauthenticated public market endpoints."""

    provider_name = "coinbase_advanced_trade"

    def __init__(self, timeout: float = 8.0,
                 opener: Callable = urlopen) -> None:
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = float(timeout)
        self._opener = opener

    @staticmethod
    def _validate_product_id(product_id: str) -> str:
        if not isinstance(product_id, str) or not _PRODUCT_ID.fullmatch(product_id):
            raise ValueError("product_id must look like BTC-USD")
        return product_id

    def _get_json(self, path: str, params: dict[str, str]) -> dict:
        url = f"{BASE_URL}/{path}?{urlencode(params)}"
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "trading-management-platform/0.1",
            },
            method="GET",
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                raw = response.read(1_048_577)
            if len(raw) > 1_048_576:
                raise MarketDataUnavailable("Provider response exceeded the 1 MiB safety limit")
            payload = json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            raise MarketDataUnavailable(
                f"Coinbase public market-data request failed with HTTP {exc.code}"
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise MarketDataUnavailable(
                f"Coinbase public market-data request failed: {type(exc).__name__}"
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidMarketData("Coinbase returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise InvalidMarketData("Coinbase response must be a JSON object")
        return payload

    def get_order_book(self, product_id: str, limit: int = 20) -> OrderBookSnapshot:
        product_id = self._validate_product_id(product_id)
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        payload = self._get_json(
            "product_book", {"product_id": product_id, "limit": str(limit)}
        )
        book = payload.get("pricebook", payload)
        if not isinstance(book, dict):
            raise InvalidMarketData("Coinbase response is missing pricebook data")
        returned_product = book.get("product_id", product_id)
        if returned_product != product_id:
            raise InvalidMarketData("Coinbase returned a different product ID")
        raw_bids, raw_asks = book.get("bids"), book.get("asks")
        if not isinstance(raw_bids, list) or not isinstance(raw_asks, list):
            raise InvalidMarketData("Coinbase order book must contain bid and ask arrays")
        bids = tuple(sorted((_level(item) for item in raw_bids),
                            key=lambda item: item.price, reverse=True)[:limit])
        asks = tuple(sorted((_level(item) for item in raw_asks),
                            key=lambda item: item.price)[:limit])
        exchange_timestamp = _timestamp(book.get("time") or payload.get("time"))
        return OrderBookSnapshot(
            provider=self.provider_name,
            product_id=product_id,
            bids=bids,
            asks=asks,
            received_at=datetime.now(timezone.utc),
            exchange_timestamp=exchange_timestamp,
        )

    def get_quote(self, product_id: str) -> MarketQuote:
        return MarketQuote.from_order_book(
            self.get_order_book(product_id, limit=1)
        )
