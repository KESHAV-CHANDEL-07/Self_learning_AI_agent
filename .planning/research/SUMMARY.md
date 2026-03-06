# Domain Research: Summary & Key Findings

## Overview
This document synthesizes findings for building a robust, continuous Python-based repository/filesystem agent in 2025.

## Key Findings

1. **Stack & Infrastructure (Confidence: HIGH)**
   - **`systemd`** is the standard for service management on Linux.
   - **`watchdog`** handles cross-platform filesystem event listening.
   - **`Typer`** paired with **`Rich`** is the modern standard for robust CLIs.
   - **`SQLite`** (with caching) is sufficient for a local agent's long-term memory.

2. **Ingestion & Analysis (Confidence: MEDIUM)**
   - **`GitPython`** is ideal for local cloning and Git operations.
   - Python's native **`ast`** module is the standard for performing static analysis on Python codebases without execution risks.

3. **Architecture (Confidence: HIGH)**
   - The system must decouple the "Observer" (watchdog) from the "Worker" (agent decision/action logic) using thread-safe queues.
   - A Plugin-based architecture for "Tasks" (sorting, cleanup, linting) is highly recommended for extensibility.

4. **Critical Pitfalls**
   - **Infinite Loops**: The agent modifying a file triggers a read event, recursively waking the agent. Strict path filtering and event-deduplication is required.
   - **Blocking I/O**: Cloning repos or heavy AST parsing must happen off the main observer thread to allow graceful shutdowns.
