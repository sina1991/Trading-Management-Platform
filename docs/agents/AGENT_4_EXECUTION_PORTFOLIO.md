# Agent 4 — Execution, Paper Trading & Portfolio

## Mission
Implement order/intent contracts, paper-only execution and portfolio accounting, consuming Strategy/Risk outputs. Build simulation before any real execution capability.

## Scope / candidate files
Execution/simulation/portfolio domain and services, paper adapter, persistence only where approved, tests, docs and ADRs. Check existing repo structure and Agent 3 contracts first.

## Responsibilities
- Define order intent/order state models and state transitions (new, accepted, rejected, partial, filled, canceled, etc.) for simulated operation.
- Implement deterministic Paper Trading adapter with configurable fee/slippage and controlled fill assumptions.
- Handle idempotency, partial fills, cancel/replace simulation, event audit and error recovery.
- Implement positions, balances/equity snapshots and realized/unrealized PnL calculations with explicit accounting assumptions.
- Design backtesting seams using historical market-data interfaces, without falsely claiming realistic fills.
- Require Risk validation before simulated execution.

## Dependencies
Agent 1 persistence/application contracts; Agent 2 market-data normalized contract; Agent 3 Strategy/Risk interfaces; Agent 0 cross-workstream coordination; Agent 6 audit.

## Acceptance Criteria
- Paper/simulation mode only; no exchange order API, signing or transaction submission.
- Deterministic tests cover lifecycle, partial fills, fees, slippage, idempotency, accounting and risk rejection.
- Monetary arithmetic precision policy documented and implemented (avoid binary float for money where appropriate).
- Event and PnL accounting reconcile with test fixtures.
- README/docs and living ledger updated with evidence and caveats.

## GitHub workflow
Feature branch and focused PR; specify simulation assumptions and exact tests; no direct main push.
