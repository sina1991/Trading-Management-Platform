# Readiness Model

Readiness is calculated per command and supports READY, PARTIAL, NOT IMPLEMENTED, MISSING FILES, MISSING DEPENDENCIES, CONFIGURATION ERROR, and DEPENDENCY ERROR.

Phase 2 metadata operations are registered as implemented and routed to the metadata command adapter. The checker verifies the required domain, persistence, service, and CLI files and requires a handler key. The CLI then opens the configured SQLite store and executes the requested service operation; adapter/database errors are reported to the operator and logged.

The storage adapter uses Python's standard-library sqlite3, so it adds no third-party runtime dependency. A READY result indicates that the implementation path and declared files are present; actual record-level validation and referential integrity are enforced at execution by services and SQLite.

Future operations (exchange connectivity, wallets, strategies, bots, execution, risk, live RPC, and market data) remain NOT IMPLEMENTED. A menu entry alone is not evidence of operational capability.
