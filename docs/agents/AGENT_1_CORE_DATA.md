# Agent 1 — Core & Data

## Mission
Maintain and close only verified gaps in Foundation, CLI, Metadata, domain/application service layers, database persistence, migrations and data integrity. Phase 1/2 are documented as complete; first audit and avoid rebuilding them.

## Scope / candidate files
`trading_platform/**` core/metadata/catalog/services/persistence/configuration/CLI modules; corresponding tests; `docs/ARCHITECTURE.md`, `docs/MODULES.md`, `docs/CLI.md`, schema/migration docs. Confirm actual paths on current main before edits.

## Responsibilities
- Verify existing command registry and readiness implementation.
- Review MetadataStore Protocol/SQLite adapter, typed domain models, CRUD, scoped relations, foreign keys, constraints, migrations, validation and recovery.
- Fix concrete defects or gaps backed by audit findings/issues.
- Keep domain and application layers independent of SQLite.
- Consider future storage adapter portability only via accepted requirements/ADR; do not introduce PostgreSQL or unnecessary infrastructure unasked.

## Dependencies
Baseline Agent 0; downstream Agents 2–5 rely on stable domain/service contracts. Coordinate breaking DTO/schema/interface changes.

## Acceptance Criteria
- Existing functionality preserved; no data reset/destructive migration.
- Relevant unit/integration tests pass; migration, integrity and backward compatibility tested for changes.
- CLI/readiness and docs accurately reflect implemented handlers.
- Security rules reject secrets/credential URLs from public metadata.
- Ledger updated with evidence and next downstream action.

## GitHub workflow
Dedicated branch, focused PR, test proof, review. Do not directly merge main.

## Not in scope
Exchange network connectivity, wallet signing, strategy algorithms, live execution, or unrelated feature additions.
