# Self-Learning AI Agent for Task Automation

## Vision
A continuous, self-learning AI agent that can ingest a GitHub repository URL or a local folder path, and intelligently automate repetitive tasks (like refactoring, organizing files, analyzing code, and cleaning up) directly on that codebase or directory. It acts as an autonomous assistant running constantly in the background.

## Core Value
The ONE thing that must work: The agent must be able to reliably accept a local path or repository URL, analyze its contents, and execute a chosen task (or learn to execute it) safely without manual intervention on every step.

## Target Users
Developers and power users who want an extensible, autonomous agent to automate maintenance, organization, and analysis of their local workspaces and code repositories.

## Technical Context
- **Language**: Python
- **Core Loop**: Perception -> Decision -> Action
- **Learning/Decision Engine**: Q-Learning (currently based on file extensions), to be upgraded to handle complex state (size, age, content) or Deep RL (DQN).
- **Architecture**: Pluggable tasks architecture (e.g., sorting, cleanup, refactoring).
- **Execution Mode**: Continuous Daemon Mode (e.g., using `watchdog` to monitor files).
- **Memory/Persistence**: robust persistent database (e.g., SQLite) to replace the current `q_table.json`.
- **Interface**: A robust Command Line Interface (CLI) (potentially using Typer or Rich) to manage tasks, view logs, and monitor learning progress.
- [Note] User confirmed the AI-proposed transition from a simple demo script to a complete, production-ready daemon architecture.

## Requirements

### Validated
(None yet — ship to validate)

### Active
- [ ] [Requirement 1] Refactor CLI to support ingesting GitHub repo URLs and local paths robustly.
- [ ] [Requirement 2] Implement Continuous Daemon Mode (directory watching).
- [ ] [Requirement 3] Create a Plugin Architecture to easily add/register new agent tasks.
- [ ] [Requirement 4] Upgrade Agent Memory to use SQLite for persistent state and logging.
- [ ] [Requirement 5] Enhance Decision Engine to interpret complex file states (e.g., age, size, type).

### Out of Scope
- [Exclusion 1] Full General Artificial Intelligence — the agent should focus on specific, actionable technical tasks (sorting, refactoring, cleanup) rather than open-ended chatting.

## Key Decisions

| Decision | Source | Rationale | Outcome |
|----------|--------|-----------|---------|
| Upgrade to Complete Project | User | The original demo script lacked the robustness needed for real-world usage on diverse repos/folders. | Decided |
| Feature: GitHub Repo / Local Path Ingestion | User | To make the agent universally applicable to any project the user is working on. | Decided |
| Feature: Daemon Mode, Plugins, SQLite, Rich CLI | AI-suggested | Necessary architectural upgrades to evolve from a PoC to a production-ready agent. | Agreed |

---
*Last updated: 2026-03-06 after initialization*
