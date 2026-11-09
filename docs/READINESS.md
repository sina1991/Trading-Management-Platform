# Readiness Model

Readiness is calculated independently for each registered command.

Supported primary statuses:

- READY
- PARTIAL
- NOT IMPLEMENTED
- MISSING FILES
- MISSING DEPENDENCIES
- CONFIGURATION ERROR
- DEPENDENCY ERROR

Planned commands return NOT IMPLEMENTED. Partial implementations return PARTIAL. Implemented commands are checked for required files, importable Python dependencies, required configuration values, configured dependency health probes, and a registered handler.

A command is executable only when the final status is READY. The checker returns supporting checks, missing items, and a human-readable reason. File existence alone does not establish readiness.

The v1 catalog deliberately marks all trading/business operations as NOT IMPLEMENTED.
