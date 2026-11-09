# Module Responsibilities

| Module | Responsibility | Phase 2 state |
|---|---|---|
| Core | Command Registry, readiness, project inspection, runtime status | Existing foundation retained |
| CLI | Menus, prompts, confirmations, safe dispatch | Integrated with metadata adapter |
| metadata.py | Typed independent domain models and validation | Implemented |
| services.py | CRUD use cases, relationship and domain validation, searches | Implemented |
| persistence.py | MetadataStore Protocol and versioned SQLite adapter | Implemented |
| metadata_cli.py | JSON prompt adapter; no business rules | Implemented |
| registries | Network, Token, Contract, ABI use cases | Routed through services |
| markets | Asset, pair, venue, market, and fee use cases | Routed through services |
| configuration | TOML configuration and storage directory selection | Existing foundation retained |
| monitoring | Logging and recent log viewing | Existing foundation retained |
| Connectors, Strategies, Bots, Execution, Risk | Future extension boundaries | Not implemented by design |

SQLite-specific SQL is isolated in `persistence.py`. The service layer depends on the repository protocol rather than the concrete database adapter.
