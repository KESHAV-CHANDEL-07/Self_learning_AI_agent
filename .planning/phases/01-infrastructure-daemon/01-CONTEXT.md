# Phase 1: Infrastructure & Daemon - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

## Phase Boundary
Establish the foundational background processes, configuration, and robust CLI.

## Implementation Decisions

### Configuration System
- **DECIDED:** "Use YAML — more readable and easier to manage lists like ignored patterns"
- **DECIDED:** "Store config globally at ~/.sg_agent/config.yaml so it works across multiple projects"
- **DECIDED:** "But also allow a local .sg_agent.yaml to override global settings if present"

### Logging Strategy
- **DECIDED:** "Rotate by SIZE (max 10MB, keep last 5 files) — more predictable for a local agent"
- **DECIDED:** "Use standard TEXT format — easier to read for now, can upgrade to JSON in V2"
- **DECIDED:** "Log location: ~/.sg_agent/logs/agent.log"

### CLI Structure
- **DECIDED:** "Command: `agent start --daemon` for clarity (makes it obvious it's running in background)"
- **DECIDED:** "Also support `agent stop`, `agent status`, `agent logs`"
- **DECIDED:** "YES to Rich — colorful output makes it much easier to see what's happening"
- **SUGGESTED:** Using Typer + Rich for the CLI framework (from previous Domain Research)

### Daemon Behavior
- **DECIDED:** "Poll every 5 seconds — better CPU usage, instant is overkill for file watching"
- **DECIDED:** "On crash: attempt AUTO-RESTART up to 3 times with exponential backoff"
- **DECIDED:** "After 3 failures, exit safely and log the fatal error clearly"

## Specific Ideas
- "Command: `agent start --daemon` for clarity"
- "Rotate by SIZE (max 10MB, keep last 5 files)"

## Deferred Ideas
- Upgrading to JSON logs is deferred to V2.

---
*Phase: 01-infrastructure-daemon*
*Context gathered: 2026-03-06*
