# Domain Research: Standard Stack (2025)

## Overview
When building a continuous, background-running Python agent that can ingest local directories or GitHub repositories in 2024/2025, the community coalesces around a few standard, battle-tested tools.

## Core Stack Components

### 1. Service Management & Daemonization (HIGH Confidence)
- **Linux/Systemd**: The absolute standard for running background Python services is using `systemd` to manage the process. It handles auto-restarts, boot initialization, and logging (`journalctl`) natively.
- **Python Daemonization**: If `systemd` isn't an option (e.g., cross-platform daemon on macOS/Windows), `python-daemon` is used for UNIX-style detachment, but `watchdog` is commonly used for the actual file-system listening loop.

### 2. Filesystem Watching & Events (HIGH Confidence)
- **`watchdog`**: The standard library for monitoring filesystem events in Python. It provides cross-platform support for detecting file creations, modifications, and deletions, which is crucial for an agent that reacts to workspace changes.

### 3. CLI Framework (HIGH Confidence)
- **`Typer`**: Typer is now the favored modern CLI framework in 2025 for new Python projects. It utilizes Python type hints to generate CLIs with minimal boilerplate and is often faster than Click.
- **`Rich`**: Often paired with Typer (and native to modern Typer versions) to provide beautiful terminal output, progress bars, and markdown rendering.

### 4. Repository Ingestion & Parsing (MEDIUM Confidence)
- **`GitPython`**: The standard choice for programmatically cloning, pulling, and interacting with GitHub or other Git repositories locally within a Python script.
- **`ast` (Built-in)**: Python's built-in `ast` module is standard for parsing Python code into Abstract Syntax Trees to analyze code structure, find functions/classes, or guide refactoring tasks without executing the code.

### 5. Persistence (HIGH Confidence)
- **`sqlite3` / `SQLAlchemy`**: For an agent needing memory across restarts (e.g., replacing a `q_table.json`), SQLite is the standard lightweight database. Often paired with `SQLAlchemy` ORM for easier structured data management representing tasks, file metadata, and learned policies.
