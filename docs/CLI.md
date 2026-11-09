# CLI Guide

Start with `python -m trading_platform`. Phase 2 uses the existing central Command Registry; each operation is shown with its readiness result and only READY commands are dispatched.

## Metadata menus

- Network: add, list, view, update, delete, validate, find by chain ID.
- Token: add, list, view, update, delete, find, validate.
- Contract: add, list, view, update, delete, validate, find by Network.
- ABI: add, list, view, update, delete, validate, link to Contract.
- Asset: add, list, view, update, delete, link Token, list Token representations.
- Trading Pair: add, list, view, update, delete, validate.
- Trading Venue: add, list, view, update, delete.
- Market: add, list, view, update, delete, validate, find by Venue, find by Trading Pair, configure fees.
- Storage: database status, schema version, integrity check.

Create and update prompts accept JSON objects. IDs are returned after creation. Use those IDs for relationships. Delete requires typing `DELETE`; database foreign keys still prevent deleting referenced entities. Errors are displayed without terminating the CLI.

The database is created lazily at `[storage].data_dir/metadata.sqlite3` (default `data/metadata.sqlite3`). It persists across restarts. No private keys or RPC credentials are accepted as metadata.

Select 0 to go back or exit. Invalid menu input is rejected.
