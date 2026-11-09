from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json

import pytest

from trading_platform.connectors.coinbase_advanced_trade import (
    BASE_URL,
    CoinbaseAdvancedTradeProvider,
)
from trading_platform.markets.market_data import (
    InvalidMarketData,
    MarketDataUnavailable,
    OrderBookLevel,
    OrderBookSnapshot,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.payload[:size]


def fake_opener(payload, captured):
    def opener(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(payload)
    return opener


def valid_payload():
    return {
        "pricebook": {
            "product_id": "BTC-USD",
            "time": "2026-11-09T12:00:00Z",
            "bids": [{"price": "65000.10", "size": "0.25"}],
            "asks": [{"price": "65001.10", "size": "0.50"}],
        }
    }


def test_coinbase_provider_uses_only_public_get_endpoint():
    captured = {}
    provider = CoinbaseAdvancedTradeProvider(
        opener=fake_opener(valid_payload(), captured)
    )
    quote = provider.get_quote("BTC-USD")
    request = captured["request"]

    assert request.method == "GET"
    assert request.full_url.startswith(BASE_URL + "/product_book?")
    assert "product_id=BTC-USD" in request.full_url
    assert request.get_header("Authorization") is None
    assert request.get_header("Cb-access-key") is None
    assert quote.bid == Decimal("65000.10")
    assert quote.ask == Decimal("65001.10")
    assert quote.spread == Decimal("1.00")
    assert quote.midpoint == Decimal("65000.60")
    assert quote.provider == "coinbase_advanced_trade"


def test_order_book_sorts_levels_and_preserves_decimal_precision():
    payload = valid_payload()
    payload["pricebook"]["bids"].append({"price": "65000.20", "size": "0.10"})
    payload["pricebook"]["asks"].append({"price": "65001.00", "size": "0.20"})
    provider = CoinbaseAdvancedTradeProvider(opener=fake_opener(payload, {}))

    book = provider.get_order_book("BTC-USD", limit=10)

    assert book.best_bid.price == Decimal("65000.20")
    assert book.best_ask.price == Decimal("65001.00")
    assert book.bids[1].price == Decimal("65000.10")
    assert book.asks[1].price == Decimal("65001.10")


@pytest.mark.parametrize("product_id", ["btc-usd", "BTCUSD", "BTC/USD", "../BTC-USD", "BTC-USD?x=1", ""])
def test_invalid_product_id_is_rejected_before_network_call(product_id):
    provider = CoinbaseAdvancedTradeProvider(opener=lambda *a, **k: pytest.fail("network called"))
    with pytest.raises(ValueError):
        provider.get_order_book(product_id)


@pytest.mark.parametrize("limit", [0, 101, True, 1.5, "10"])
def test_invalid_order_book_limit_is_rejected(limit):
    provider = CoinbaseAdvancedTradeProvider(opener=lambda *a, **k: pytest.fail("network called"))
    with pytest.raises(ValueError):
        provider.get_order_book("BTC-USD", limit=limit)


def test_malformed_book_is_rejected():
    payload = {"pricebook": {"product_id": "BTC-USD", "bids": [], "asks": []}}
    provider = CoinbaseAdvancedTradeProvider(opener=fake_opener(payload, {}))
    with pytest.raises(InvalidMarketData):
        provider.get_order_book("BTC-USD")


def test_crossed_book_is_rejected():
    payload = valid_payload()
    payload["pricebook"]["asks"][0]["price"] = "65000.00"
    provider = CoinbaseAdvancedTradeProvider(opener=fake_opener(payload, {}))
    with pytest.raises(InvalidMarketData):
        provider.get_order_book("BTC-USD")


def test_non_finite_and_non_positive_levels_are_rejected():
    with pytest.raises(InvalidMarketData):
        OrderBookLevel(Decimal("NaN"), Decimal("1"))
    with pytest.raises(InvalidMarketData):
        OrderBookLevel(Decimal("1"), Decimal("0"))


def test_stale_snapshot_uses_exchange_timestamp():
    now = datetime(2026, 11, 9, 12, 1, tzinfo=timezone.utc)
    old = now - timedelta(seconds=30)
    book = OrderBookSnapshot(
        provider="test",
        product_id="BTC-USD",
        bids=(OrderBookLevel(Decimal("99"), Decimal("1")),),
        asks=(OrderBookLevel(Decimal("101"), Decimal("1")),),
        received_at=now,
        exchange_timestamp=old,
    )
    assert book.is_stale(max_age_seconds=10, now=now)
    assert not book.is_stale(max_age_seconds=60, now=now)


def test_provider_timestamp_must_be_timezone_aware():
    payload = valid_payload()
    payload["pricebook"]["time"] = "2026-11-09T12:00:00"
    provider = CoinbaseAdvancedTradeProvider(opener=fake_opener(payload, {}))
    with pytest.raises(InvalidMarketData):
        provider.get_order_book("BTC-USD")


def test_response_must_match_requested_product():
    payload = valid_payload()
    payload["pricebook"]["product_id"] = "ETH-USD"
    provider = CoinbaseAdvancedTradeProvider(opener=fake_opener(payload, {}))
    with pytest.raises(InvalidMarketData):
        provider.get_order_book("BTC-USD")


def test_quote_spread_basis_points_are_computed_without_float_rounding():
    provider = CoinbaseAdvancedTradeProvider(opener=fake_opener(valid_payload(), {}))
    quote = provider.get_quote("BTC-USD")
    assert quote.spread_bps == Decimal("1.00") / Decimal("65000.60") * Decimal("10000")


def test_invalid_json_is_rejected():
    class BrokenResponse(FakeResponse):
        def read(self, size=-1):
            return b"not-json"
    provider = CoinbaseAdvancedTradeProvider(opener=lambda *a, **k: BrokenResponse({}))
    with pytest.raises(InvalidMarketData):
        provider.get_order_book("BTC-USD")


def test_response_size_is_bounded():
    class LargeResponse(FakeResponse):
        def read(self, size=-1):
            return b" " * 1_048_577
    provider = CoinbaseAdvancedTradeProvider(opener=lambda *a, **k: LargeResponse({}))
    with pytest.raises(MarketDataUnavailable):
        provider.get_order_book("BTC-USD")
