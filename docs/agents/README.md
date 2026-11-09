# Multi-Agent Implementation Playbook

Repository: https://github.com/sina1991/Trading-Management-Platform
Default branch: `main`
Playbook branch: `docs/agent-handoff-and-implementation-playbook`

## Purpose
These role prompts organize completion work into bounded, reviewable tasks. Read the shared living ledger before acting. Do not assume a prompt's work is still outstanding: verify the live repository, open PRs, merged PRs, CI, and ledger first.

## Agent prompts
- [Agent 0 — Lead / Orchestrator](AGENT_0_ORCHESTRATOR.md)
- [Agent 1 — Core & Data](AGENT_1_CORE_DATA.md)
- [Agent 2 — Exchange & Wallet Infrastructure](AGENT_2_EXCHANGE_WALLET.md)
- [Agent 3 — Strategy & Risk](AGENT_3_STRATEGY_RISK.md)
- [Agent 4 — Execution & Portfolio / Simulation](AGENT_4_EXECUTION_PORTFOLIO.md)
- [Agent 5 — API & UI](AGENT_5_API_UI.md)
- [Agent 6 — Independent QA & Security](AGENT_6_QA_SECURITY.md)

## Shared files
- [Living implementation ledger](IMPLEMENTATION_STATE.md) — authoritative task status and handoff notes.
- [Reusable new-chat bootstrap prompt](NEW_AGENT_BOOTSTRAP_PROMPT.md) — paste at the start of every agent chat.

## Required protocol
1. Bootstrap prompt first; inspect state rather than blindly executing assigned scope.
2. Use a dedicated branch per task and PR to `main`; never push directly to `main`.
3. Avoid overlapping file ownership. Coordinate shared contracts through Agent 0.
4. Update `IMPLEMENTATION_STATE.md` in the same PR as implementation, with evidence and remaining work.
5. Agent 6 audits implementation independently; it must not approve its own implementation.
6. No live trading, wallet signing, transaction submission, or real-money operation without a separate explicit user authorization and prior security gate.
7. A task is complete only when its Acceptance Criteria pass and CI results are documented. A merged PR alone is not proof of runtime acceptance.
