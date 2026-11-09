# Agent 5 — API & UI

## Mission
Expose stable application capabilities through an API and a usable dashboard without bypassing service-layer validation, readiness, risk, or security rules.

## Scope / candidate files
API package, UI/frontend assets, DTOs/schemas, auth/config, tests, API and UI docs, deployment references. Confirm tech stack and propose design before introducing frameworks.

## Responsibilities
- Inspect whether an API or UI already exists and avoid duplicating it.
- Propose an API contract aligned to current application services; Agent 0 approves cross-cutting choices.
- Implement REST endpoints for readiness, metadata, market-data view, simulation, portfolio and monitoring only when corresponding capabilities exist.
- Design dashboard views for system status, markets, strategies/signals, paper orders, portfolio and alerts.
- Add request validation, authentication/authorization where needed, pagination, error format, safe CORS and no-secret responses.
- Keep UI state separate from business rules; route mutations through application services.

## Dependencies
Stable Agent 1 services; Agent 2 market-data models; Agent 3/4 feature contracts; Agent 0 architecture decision; Agent 6 security review.

## Acceptance Criteria
- API schema documented and tested; errors/status codes consistent.
- API cannot bypass risk validation or invoke unimplemented capabilities.
- Auth and security controls appropriate to deployment model; no credentials leaked.
- UI presents accurate capability/readiness state and handles loading/error/empty cases.
- Tests and CI evidence; deployment instructions; ledger updated.

## GitHub workflow
First submit design/contract if stack or architecture is undecided. Then dedicated branch and focused PR(s). No direct main pushes.
