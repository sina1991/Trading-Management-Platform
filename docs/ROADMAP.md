# Roadmap

## Phase 1 — Foundation (v1)

- [x] Python package and Modular Monolith foundation
- [x] Interactive CLI and complete menu catalog
- [x] Central Command Registry
- [x] Per-command Readiness Checker
- [x] Project Structure Inspector
- [x] System Status
- [x] Configuration and logging foundations
- [x] Automated tests and CI workflow
- [x] Documentation and agent handoff

## Phase 2 — Metadata and persistence

Implement safe metadata management for venues, networks, tokens, contracts, ABIs, assets, trading pairs, and market definitions. Do not imply live connectivity.

## Phase 3 — Strategy and Bot management

Implement strategy definitions and independent Bot Instance metadata/lifecycle state. No algorithmic trading execution without a separately authorized phase.

## Phase 4 — Risk and simulation

Define risk validation and deterministic simulation/paper-execution contracts. Keep Strategy, Risk, and Execution independent.

## Phase 5 — External integrations (requires explicit approval)

Only after separate approval: exchange/DEX adapters, network/RPC, wallet integration, and real execution. Security review, threat model, credential handling, and safety controls are prerequisites.
