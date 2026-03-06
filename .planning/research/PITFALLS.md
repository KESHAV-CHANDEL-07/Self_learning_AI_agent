# Domain Research: Common Pitfalls

## What Projects in this Domain Get Wrong

### 1. Infinite Trigger Loops (HIGH Risk)
- **The Problem**: The agent modifies a file (e.g., sorts it or appends a comment), which triggers a filesystem "modified" event, which wakes the agent up to process the file again, creating an infinite loop.
- **The Solution**: Maintain an internal cache of recently modified files by the agent itself, or pause the `watchdog` observer during the Action phase.

### 2. Ignoring `.gitignore` / Hidden Files (MEDIUM Risk)
- **The Problem**: The agent mistakenly analyzes or moves files in `.git/`, `__pycache__/`, or `node_modules/`, corrupting repositories or wasting massive amounts of compute.
- **The Solution**: Implement a robust path-filtering utility that strictly adheres to standard ignore patterns *before* the Perception phase.

### 3. Blocking the Main Event Loop (HIGH Risk)
- **The Problem**: If an action (like cloning a large GitHub repo or running a heavy AST parsing job) runs synchronously, it blocks the agent from responding to shutdown signals or logging health checks.
- **The Solution**: Offload heavy actions to background threads/processes (`concurrent.futures.ThreadPoolExecutor` or `asyncio`).

### 4. Silent Failures & Poor Observability (MEDIUM Risk)
- **The Problem**: Background daemons lack standard out (STDOUT) visibility by default. If the agent hits an exception and dies, the user won't know unless they manually check.
- **The Solution**: Implement robust exception catching at the top level of the worker thread, combined with reliable file-based logging and (if applicable) OS-level notifications or CLI health-check commands.
