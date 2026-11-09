# Architecture

## Architecture style

The initial release is a Python Modular Monolith. The CLI and application services run in one process. No microservices, message queue, database server, or live trading service is introduced.

## Boundaries and dependency direction

- CLI is the presentation/interaction layer. It depends on the central command catalog, core contracts, configuration, and monitoring services.
- Core owns command metadata, registry validation, readiness evaluation, project inspection, and runtime status.
- Configuration owns loading and validation of configuration.
- Monitoring owns application logging and log presentation.
- Future domain boundaries are Connectors, Blockchain Registries, Markets, Strategies, Bots, Execution, Risk, and Storage. They must remain independent of CLI presentation and must collaborate through explicit contracts.
- Strategy logic must not be coupled to Bot lifecycle or Execution.
- CEX and DEX markets must remain venue-specific.
- A Token, Contract, ABI, and Network are separate concepts.

## Readiness truth

A command is READY only when it is marked implemented, required files and dependencies are present, required configuration is valid, dependency probes pass, and an execution handler is registered. A menu entry or file alone is never proof of functionality.

## Configuration

The sample configuration uses TOML. Python 3.11+ provides tomllib; Python 3.10 uses tomli. Secrets are not stored in the sample configuration.

## v1 exclusions

No live KuCoin, Uniswap, PancakeSwap, wallet, RPC, blockchain transaction, algorithmic strategy, order execution, or real-money trading is implemented.
