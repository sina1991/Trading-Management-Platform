# Phase A — Read-only market data

## Provider decision

Phase A uses the **Coinbase Advanced Trade public market-data API**. Its public
market endpoints do not require authentication. The adapter uses only:

- `GET /api/v3/brokerage/market/product_book` for public order-book snapshots.

The base URL is fixed to `https://api.coinbase.com/api/v3/brokerage/market`.
It is not user-configurable, which avoids turning the provider adapter into an
arbitrary HTTP client.

Official documentation:
- [Public Get Product Book](https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/public/get-public-product-book)
- [Advanced Trade API endpoint overview](https://docs.cdp.coinbase.com/advanced-trade/docs/rest-api-overview)

## Implemented contract

- Provider-neutral `MarketDataProvider` protocol.
- Normalized immutable `OrderBookSnapshot`, `OrderBookLevel`, and
  `MarketQuote` value objects.
- Decimal arithmetic for price, size, midpoint, spread, and spread basis points.
- Product-ID validation before any network request.
- Explicit GET method, bounded timeout, bounded response size, and JSON/type checks.
- Invalid, empty, crossed, stale, or mismatched snapshots are not treated as
  valid executable quotes.
- CLI actions display a public quote or order-book snapshot only.

## Safety boundary

This integration is strictly read-only:

- No API key, secret, passphrase, account identifier, or authorization header.
- No authenticated/private Coinbase endpoints.
- No POST, PUT, PATCH, or DELETE request path.
- No account balances, transfers, deposits, withdrawals, wallet signing,
  transaction submission, order creation, order cancellation, or execution.
- No strategy decision or automatic trade is triggered by receiving a quote.
- No market data is persisted or used to authorize a trade.

This is a data-ingestion foundation, not a trading system. Public market-data
availability and Coinbase's terms/rate limits remain external dependencies.
Quotes are snapshots and can become stale immediately after retrieval.

## Local usage

From the repository root:

```bash
python -m trading_platform
```

Open **Market Management** and select **Fetch Best Bid/Ask** or
**Fetch Public Order Book**. Enter a product such as `BTC-USD`.

The adapter can also be used directly:

```python
from trading_platform.connectors.coinbase_advanced_trade import (
    CoinbaseAdvancedTradeProvider,
)

provider = CoinbaseAdvancedTradeProvider()
quote = provider.get_quote("BTC-USD")
print(quote.bid, quote.ask, quote.spread_bps)
```

## Verification

The adapter tests use a deterministic fake HTTP transport and do not call
Coinbase. A live provider smoke test is deliberately kept separate from the
unit-test suite so CI does not depend on exchange availability.


## Timestamp validation and freshness

The Coinbase Product Book response must contain a non-empty `product_id`
matching the requested product and a usable exchange timestamp. The timestamp
must be a non-empty ISO-8601 string with an explicit timezone; missing, empty,
malformed, or timezone-naive values are rejected as `InvalidMarketData`.
The provider does not substitute the requested product identifier or local
receipt time for missing response fields.

`OrderBookSnapshot.age_seconds(now)` measures age using the exchange timestamp
only. If the exchange timestamp is unknown, it returns `None`; it does not
fall back to `received_at`. `is_stale()` correspondingly returns `None` for
unknown freshness. A timestamp later than the timezone-aware reference time is
invalid and raises `InvalidMarketData`, never clamped to age zero. No clock-skew
tolerance is applied. Local receipt time remains recorded independently.

The CLI quote and order-book output includes **Exchange timestamp**, **Local
receipt time**, and **Data age / freshness**. Unknown exchange time is shown as
`UNKNOWN`; future or timezone-invalid data is shown as `INVALID`.

## HTTP redirect policy

The public adapter's HTTP opener rejects redirects rather than following them,
so a response cannot redirect the GET request to an unexpected host. The fixed
Coinbase API base URL and GET-only request method remain unchanged.

## Deterministic test commands

Run the complete suite without live Coinbase access:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

The GitHub Actions workflow `.github/workflows/tests.yml` runs this suite on
Python 3.10, 3.11, and 3.12. Tests use a fake HTTP transport; no credentials or
live exchange smoke test are required or claimed.
