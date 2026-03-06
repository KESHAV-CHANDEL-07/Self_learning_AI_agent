# Domain Research: Common Features

## Overview
Products in the domain of autonomous coding/filesystem agents tend to share a set of expected features that separate toys from production tools.

## Table Stakes (Expected Features)
- **Continuous Monitoring**: The ability to run in the background and watch a directory for changes without manual triggers (Daemon mode).
- **Graceful Shutdown**: Ability to intercept `SIGTERM` / `SIGINT` to safely save state (e.g., Q-table or DB) before exiting.
- **Configuration Management**: Externalized settings (e.g., `.env` files, `config.yaml`) for setting ignore paths, polling intervals, and API keys.
- **Robust Logging**: Comprehensive logging to files with rotation, keeping a history of all actions the agent took.
- **Local Git Support**: Ingesting and acting upon local Git repositories (respecting `.gitignore`).

## Differentiating Features (Advanced)
- **Plugin System**: Dynamically loading new "Skills" or "Tasks" (e.g., a new refactoring module) without rewriting core agent logic.
- **Remote Repo Ingestion**: Accepting a GitHub URL, cloning it to a temporary/managed workspace, and analyzing it seamlessly.
- **Complex State Representation**: Using AST analysis, token counts, or vector embeddings of files rather than simple file extensions to make decisions.
- **Interactive CLI Dashboard**: Using tools like `Rich` to show real-time views of the agent's memory, learning curve, and current queued tasks.
