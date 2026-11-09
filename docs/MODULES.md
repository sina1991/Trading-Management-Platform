# Module Responsibilities

| Area | v1 responsibility | State |
|---|---|---|
| Core | Command Registry, Readiness Checker, Project Structure Inspector, System Status | Implemented |
| CLI | Main menu, all requested submenus, safe command dispatch | Implemented |
| Configuration | TOML loading, environment log-level override, validation | Implemented |
| Monitoring | File logging and recent log viewing | Implemented |
| Connectors | Future CEX/DEX/network/wallet/RPC adapter boundary | Planned |
| Registries | Independent Network, Token, Contract, ABI registries | Planned |
| Markets | Assets, trading pairs, venue-specific markets and fees | Planned |
| Strategies | Strategy definitions and extension contract | Planned |
| Bots | Independent bot identity, configuration and lifecycle | Planned |
| Execution | Orders, transactions, routing and status boundary | Planned |
| Risk | Independent pre-execution validation boundary | Planned |
| Storage | Persistence abstraction boundary | Planned |

A package/menu boundary does not mean future business functionality is operational. Planned operations remain NOT IMPLEMENTED.
