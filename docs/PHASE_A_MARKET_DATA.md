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
