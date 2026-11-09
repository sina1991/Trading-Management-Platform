# Agent 2 — Exchange & Wallet Infrastructure

## Mission
Build a safe adapter foundation for Exchange public market data and read-only wallet/network information. Start with the smallest public/read-only vertical slice; integrations are not authorized for trading.

## Scope / candidate files
Create/extend dedicated adapter modules and interfaces under the existing package conventions; tests, configuration docs, dependency declarations and integration documentation. Inspect repo and propose file ownership before creating new architecture.

## Responsibilities
- Define provider interfaces and normalized data models for public ticker, order book, trades, OHLCV, health and error/rate-limit behavior.
- Implement one explicitly scoped public read-only Exchange adapter (Coinbase Public Market Data if still the chosen approved task; inspect PR #4 and branch state first).
- Design read-only wallet/network balance/holdings interfaces only if RPC/provider scope and network are specified and approved.
- Handle timeout, retries with bounded backoff, rate limits, stale data, validation and provider outages.
- Establish secret references and safe config patterns; never persist or log secrets.
- Document capability flags so unsupported provider operations are never advertised as READY.

## Dependencies
Agent 1 stable services/domain conventions; Agent 0 accepted adapter contract; Agent 6 security/test review. Check existing Coinbase PRs to avoid duplication.

## Acceptance Criteria
- No signing, private-key handling, transaction submission, order placement, or live trading.
- Adapter contract tests and mocked unit tests; integration tests are optional, public-only and safely gated.
- Normalized types and errors; deterministic handling of malformed/provider error responses.
- Timeouts/rate limits and safe logs verified.
- Config and docs show no secret values; readiness accurately reflects capability.
- Ledger includes PR, tests, and remaining providers.

## GitHub workflow
One provider or capability per PR; dedicated branch from latest main; no direct main pushes. Cite Actions CI.

## Out of scope
Strategy logic, order execution, wallet signing, chain transactions, broad multi-exchange rollout absent milestone acceptance.
