# Agent 3 — Strategy & Risk

## Mission
Implement strategy definitions, signal contracts, lifecycle metadata, and deterministic risk controls. Begin with no real order execution.

## Scope / candidate files
Strategy and risk domain/application modules, schemas/config, CLI or service integration, tests, ADR/contracts and relevant docs. Confirm current structure before file creation.

## Responsibilities
- Audit roadmap Phase 3 and existing strategy/bot metadata before implementing.
- Separate Strategy Definition, Strategy Instance, Bot lifecycle and generated Signal concepts.
- Specify validated strategy configuration and lifecycle transitions.
- Define deterministic Risk interface and rules (e.g. max notional/position/exposure, daily loss, slippage/liquidity guard thresholds) only as configurable, explicit policies.
- Ensure Risk can reject an intent with machine-readable reason and auditable event.
- Define interfaces for downstream Agent 4 without coupling strategy algorithms to exchange execution.

## Dependencies
Agent 1 domain/service contracts; Agent 2 normalized market data interface; Agent 0 interface decisions; Agent 4 consumes Strategy/Risk contracts.

## Acceptance Criteria
- No actual orders or funds movement.
- Validation and lifecycle transitions have test coverage, including invalid transitions and boundary conditions.
- Risk results deterministic for same input/config and fail-closed on missing required risk data.
- Strategy, Risk and Execution remain independently testable.
- Documentation and ledger describe interfaces, limitations and next downstream steps.

## GitHub workflow
Dedicated feature branch and focused PR. Record API/contract decisions (ADR if cross-cutting); CI proof required.
