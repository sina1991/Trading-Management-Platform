# Architecture

## Style and dependency direction

The application remains a Python Modular Monolith. CLI is the presentation layer; application services enforce use-case and relationship rules; domain models contain typed data and local validation; the `MetadataStore` Protocol is the storage port; `SQLiteStore` is the initial adapter. Domain and application services do not import SQLite.

```
CLI / Command Registry
        |
MetadataCLI adapter
        |
MetadataService (application validation)
        |
MetadataStore Protocol
        |
SQLiteStore adapter -> SQLite database
```

## Domain entities

- Blockchain: Network, Token, Contract, ABI.
- Trading: Asset, TradingPair, TradingVenue, Market.
- Fees: FeeMetadata with separate CEX maker, CEX taker, DEX pool, and network gas fields.

All entities use stable UUID identifiers by default and UTC ISO-8601 creation/update timestamps. Models provide dictionary serialization and deserialization. Display names and symbols are not primary identifiers.

## Relationships

- Token -> Network (required); Token -> Contract (optional, network must match).
- Contract -> Network (required); Contract -> ABI (optional). ABI is independent and may be reused.
- TradingPair -> base Asset and quote Asset (both required and distinct).
- Asset <-> Token is many-to-many through `asset_tokens`.
- Market -> TradingVenue and TradingPair (required); optional Network and pool Contract.
- DEX Markets require a Network; CEX Markets reject DEX pool fields.
- FeeMetadata -> Market; CEX and DEX fee categories are validated separately.

## Persistence

SQLite is selected because it is embedded, free, and available in the Python standard library. Tables use stable primary keys, foreign keys, uniqueness constraints, JSON text for extensible metadata/ABI definitions, and timestamps. Foreign-key enforcement, busy timeout, and WAL journaling are enabled per connection. Schema version is stored in `schema_version`; version 1 is an additive initial migration and never drops user tables.

Tables: `networks`, `tokens`, `contracts`, `abis`, `assets`, `trading_pairs`, `venues`, `markets`, `fee_metadata`, `asset_tokens`, `schema_version`.

Uniqueness: chain ID; contract address scoped by network; native token symbol scoped by network; contract token symbol scoped by network and contract; base/quote asset pair; venue/pair market; one fee record per market.

## Validation and safety

Models validate required fields and types. Services validate references and cross-entity invariants. SQLite foreign keys protect integrity when the CLI is bypassed. EVM-style addresses are checked for the 20-byte hexadecimal format. Public metadata rejects credential-like keys; Network RPC configuration stores a reference only, never an RPC URL.

## Migration and recovery

Migrations are versioned and run within SQLite transactions. Startup creates missing schema only; it never resets or replaces an existing database. Back up the database before upgrades. Stop the process and close/checkpoint WAL before copying a standalone database file; if copying live, retain associated WAL/SHM files. Restore only from a verified backup with the application stopped.

## Explicit exclusions

No live exchange, DEX, RPC, wallet, signing, transaction, market-data, strategy, bot-execution, or real-money capability is part of Phase 2.
