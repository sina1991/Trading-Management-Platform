# Trading Management Platform

An independent Python Modular Monolith foundation for managing and extending multiple Trading Bots. This is a management platform, not a single trading bot.

## Requirements

- Python 3.10+
- No live exchange, blockchain node, wallet, database server, or external API is required for v1.

## Quick start

    python -m venv .venv
    . .venv/bin/activate
    python -m pip install -e ".[dev]"
    python -m trading_platform

Windows PowerShell activation:

    .venv\Scripts\Activate.ps1

Run tests:

    pytest -q

## Implemented foundation

- Interactive CLI and complete v1 menu catalog.
- Central Command Registry.
- Per-operation Readiness Checker with seven explicit status labels.
- Safe dispatch: only READY operations with registered handlers execute.
- Project Structure Inspector and System Status.
- TOML configuration loading and validation.
- File-based logging.
- Automated tests and GitHub Actions workflow.

## Not implemented in v1

Live CEX/DEX connectivity, Wallet operations, blockchain transactions, trading algorithms, bot lifecycle execution, order execution, and real-money trading are explicitly excluded. Their menu operations remain visible and report NOT IMPLEMENTED.

See docs/ for architecture, module responsibilities, CLI, readiness, and roadmap. PROGRESS.md is the agent handoff record. Never commit credentials or secrets.
