# Project State

## Current Position
**Phase:** 3 — Core Capabilities & Memory
**Status:** Complete
**Last activity:** 2026-03-09 — Phase 3 executed (SQLite DAO, plugins, tests)

## Key Decisions

| Decision | Phase | Source | Rationale |
|----------|-------|--------|-----------|
| Extend V1 with robust logging, error handling, configs, and tests | Init | User | Necessary for a truly complete, production-ready project before adding advanced AI features. |
| Use Typer + Rich + SQLite + Watchdog | Init | AI-suggested | The most robust, modern Python stack for this domain. |
| Config: YAML, global `~/.sg_agent/` with local overrides | 1 | User | YAML is readable, global allows cross-project usage. |
| Logs: Size rotated (10MB x 5), Text format, stored in `~/.sg_agent/logs/` | 1 | User | Predictable storage usage, text is easier for V1 readability. |
| CLI: `agent start --daemon`, colorful Rich output | 1 | User | Clarity on background status, Rich improves visibility. |
| Daemon: 5s poll, auto-restart 3x with backoff, then safe exit | 1 | User | Balances CPU usage with robust error recovery. |
| Repos: Managed workspaces at `~/.sg_agent/workspaces/`, `git pull` if exists, persistent storage. | 2 | User | Ensures persistence and simple update mechanism vs re-cloning. |
| Path filtering: Mixed approach (defaults + global/local config + `.gitignore`). | 2 | User | Offers maximum flexibility for ignoring folders like node_modules or .git. |
| Plugins: Single file per plugin in `~/.sg_agent/plugins/`, auto-discovered, specific interface. | 2 | User | Simplifies plugin creation and usage with zero manual registration. |
| Error/Shutdown: 10s graceful timeout, 3x retry on clone, skip on permission errors. | 2 | User | Prevents crashes on long/dirty operations or locked files. |
| SQLite for Memory: Store Q-values in learning.db | 3 | AI-suggested | Provides persistent, thread-safe, resilient storage vs JSON dictionary. |

### Blockers/Concerns
None

---
*Last updated: 2026-03-06*
