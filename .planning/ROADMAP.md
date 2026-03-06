# Roadmap

## Milestone 1: Core Agent V1 (Production Ready)

### Progress

| Phase | Name | Status | Plans | Date |
|-------|------|--------|-------|------|
| 1 | Infrastructure & Daemon | Planned | — | — |
| 2 | Ingestion & Architecture | Planned | — | — |
| 3 | Core Capabilities & Memory | Planned | — | — |

### Phases

#### Phase 1: Infrastructure & Daemon
**Goal:** Establish the foundational background processes, configuration, and robust CLI.
**Requirements:** [R1, R3, R8, R10]
- [ ] Implement `config.yaml` support for path and log level configuration.
- [ ] Setup structured file-based logging.
- [ ] Build base `Typer`/`Rich` CLI with basic start/stop commands.
- [ ] Implement `watchdog` daemon loop capable of running continuously in the background.

#### Phase 2: Ingestion & Architecture
**Goal:** Enable the agent to safely ingest local/remote repositories and support extensible behaviors.
**Requirements:** [R2, R4, R6, R7, R9]
- [ ] Integrate `GitPython` to clone and manage remote GitHub URLs locally.
- [ ] Implement strict path filtering (e.g., ignoring `.git/`, `node_modules/`).
- [ ] Create the Plugin Task architecture (BaseTask interface and Plugin Registry).
- [ ] Implement graceful shutdown signal handling (`SIGTERM`).
- [ ] Add robust error handling for missing paths and Git clone failures.

#### Phase 3: Core Capabilities & Memory
**Goal:** Connect the decision engine to a persistent database and ensure the system is stable.
**Requirements:** [R5, R11]
- [ ] Replace `q_table.json` logic with a lightweight `SQLite` database for state and history.
- [ ] Port the existing "File Sorting" and "Cleanup" tasks to the new Plugin Architecture.
- [ ] Write unit tests for CLI, Plugin Registry, and SQLite Data Access Object (DAO).
- [ ] End-to-end testing of the complete flow.

---
*Last updated: 2026-03-06*
