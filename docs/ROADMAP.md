# Roadmap

## Phase 1 — Foundation

- [x] Python Modular Monolith and package structure
- [x] CLI, central Command Registry, evidence-based readiness
- [x] Configuration, logging, structure inspection, CI

## Phase 2 — Metadata and persistence

- [x] Typed Network, Token, Contract, ABI, Asset, TradingPair, TradingVenue, Market, FeeMetadata models
- [x] Network-scoped token and contract identities
- [x] Reusable ABI definitions and contract linkage
- [x] Asset-to-token many-to-many association
- [x] Venue-specific CEX/DEX market metadata and distinct fee fields
- [x] SQLite repositories, schema version, foreign keys, CRUD and integrity checks
- [x] CLI integration through the existing Command Registry
- [x] Automated verification on Python 3.10, 3.11, and 3.12 (30 tests passed in each CI job)

## Phase 3 — Strategy and Bot metadata

Implement strategy definitions and independent Bot Instance metadata/lifecycle state. No algorithmic trading execution.

## Phase 4 — Risk and simulation

Define risk validation and deterministic simulation/paper-execution contracts. Keep Strategy, Risk, and Execution independent.

## Phase 5 — External integrations (separate authorization required)

Only after explicit approval: exchange/DEX adapters, network/RPC, wallet integration, and real execution. Security review, threat model, credential handling, and safety controls are prerequisites.
