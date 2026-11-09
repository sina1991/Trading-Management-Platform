# Trading Management Platform

An independent Python Modular Monolith for managing trading metadata and, in later phases, multiple trading bots. This is a management platform, not a single bot.

## Requirements and setup

- Python 3.10+
- SQLite (included in Python's standard library)
- No live exchange, blockchain node, wallet, paid API, or external service is required.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python -m trading_platform
pytest -q
```

## Phase 2 metadata and persistence

Phase 2 adds typed models and SQLite-backed CRUD for Networks, Tokens, Contracts, ABIs, Assets, Trading Pairs, Trading Venues, Markets, and distinct fee metadata. The CLI exposes the operations through the existing Command Registry and Readiness Checker.

The default database is `data/metadata.sqlite3` (controlled by `[storage].data_dir` in TOML configuration). The database is created on first metadata command and is not deleted or reset at startup. Schema version 1 is recorded in the database. Foreign keys are enabled on every connection.

Metadata create/update prompts accept a JSON object, for example:

```json
{"name":"Ethereum","chain_id":1,"network_type":"evm","native_currency":"ETH","status":"active"}
```

Identifiers are generated as UUIDs unless explicitly supplied. Use returned IDs when creating relationships. A Token is network-scoped; a Contract address is unique only within its Network; an Asset is an economic concept and can be associated with multiple Token records.

## Safety and backup

- Never put RPC URLs containing credentials, API keys, passwords, private keys, or access tokens in metadata.
- `rpc_config_ref` is a reference to a future secure configuration mechanism, not a URL.
- Before schema upgrades or manual database maintenance, stop the application and copy the complete database file. With WAL enabled, checkpoint/close the database before copying; retain the `-wal` and `-shm` files if copying while open.
- Restore by stopping the application and replacing the database file with a verified backup. Do not delete the database to resolve migration errors.

## Scope exclusions

No live exchange/DEX connectivity, wallet signing, live RPC, blockchain transaction submission, live market data, strategies, bot execution, order execution, or real-money trading is implemented in Phase 2. These remain future work.

See `docs/` for architecture, schema, CLI, readiness, decisions, and roadmap. `PROGRESS.md` records the verified repository state.
