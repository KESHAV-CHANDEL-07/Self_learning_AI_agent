# Domain Research: Architecture Patterns

## Typical Structures for Background Agents

### 1. The Event-Driven Loop
Instead of a simple `while True` loop that sleeps, modern agents use an event-driven architecture.
- **Observer**: A `watchdog` observer monitors the filesystem and places events (e.g., `FileCreated`, `FileModified`) into a Thread-safe Queue.
- **Worker/Consumer**: A background thread or async task pops events from the Queue and feeds them into the Agent's Perception-Decision-Action pipeline.

### 2. The Plugin Architecture
To keep the core agent lightweight, specific tasks are abstracted into plugins.
- **Task Interface**: A base class (abstract class) defining `evaluate_state()`, `get_possible_actions()`, and `execute_action()`.
- **Registry**: The agent dynamically loads available tasks from a designated `plugins/` or `tasks/` directory at startup.

### 3. The Memory Layer
- **State Separation**: Keeping short-term memory (the current queue of files to process) separate from long-term memory (the learned Q-table or SQLite database tracking historical reward metrics).
- **Data Access Object (DAO)**: Abstracting the persistence logic (reading/writing to SQLite) so the core Decision engine isn't tied directly to SQL queries.

### 4. Graceful Lifecycle Management
- **Signal Handlers**: Registering Python's `signal.signal(signal.SIGTERM, handler)` to ensure that if the daemon is killed, the queue is drained and the database/Q-table is flushed to disk.
