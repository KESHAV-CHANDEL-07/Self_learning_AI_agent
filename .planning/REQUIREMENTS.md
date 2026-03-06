# Requirements

## Overview
These requirements define the transition of the Self-Learning AI Agent from a local demo script to a complete, robust project capable of ingesting URLs, operating as a background daemon, and supporting extensible task plugins.

## V1 — Must Have
These are table stakes. The product doesn't work without them.

| ID | Requirement | Phase | Status |
|----|-------------|-------|--------|
| R1 | **CLI Upgrade**: Implement a `Typer` & `Rich` based CLI capable of accepting a local path or a GitHub URL. | TBD | Planned |
| R2 | **Repo Ingestion**: Capability to clone a remote GitHub URL to a managed local workspace using `GitPython`. | TBD | Planned |
| R3 | **Daemon Mode**: Implement a continuous background listener using `watchdog` to monitor workspaces. | TBD | Planned |
| R4 | **Plugin Architecture**: Abstract the decision/action loop so new tasks (beyond sorting/cleanup) can be registered easily. | TBD | Planned |
| R5 | **Persistent Memory**: Replace `q_table.json` with an `SQLite` database for maintaining the agent's models and historical logs. | TBD | Planned |
| R6 | **Graceful Shutdown**: Intercept termination signals to safely flush queues and database writes before exiting. | TBD | Planned |
| R7 | **Path Filtering**: Implement robust ignoring of patterns like `.git`, `__pycache__`, and `node_modules` to prevent infinite loops and wasted compute. | TBD | Planned |
| R8 | **Logging**: Add structured logging to a file using Python's logging module, logging all agent decisions, file events, and errors with timestamps. | TBD | Planned |
| R9 | **Error Handling**: Gracefully handle invalid URLs, failed GitHub clones, missing paths, and permission errors with clear user-friendly messages. | TBD | Planned |
| R10 | **Config File**: Add `config.yaml` or `.env` support for settings like workspace path, ignored patterns, log level, and plugin toggles. | TBD | Planned |
| R11 | **Basic Testing**: Write unit tests for CLI commands, plugin registration, and database read/write operations. | TBD | Planned |

## V2 — Nice to Have
Differentiators and improvements for after v1 is stable.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| R12 | **Advanced AST Decisions**: Upgrade the decision model to parse Python ASTs instead of just file extensions. | High | Backlog |
| R13 | **Deep RL (DQN)**: Replace tabular Q-learning with a neural network approach if state spaces become too large. | Medium | Backlog |
| R14 | **Systemd Unit Generator**: A CLI command to generate a Linux `systemd` service file for easy production deployment. | Low | Backlog |

## Out of Scope
- A graphical user interface (GUI) or web dashboard. All interactions will happen via the interactive CLI and log files.

---
*Last updated: 2026-03-06*
