# Phase 1: Infrastructure & Daemon — Research

## Implementation Approach
The agent will be structured with a robust background daemon running `watchdog` to monitor workspaces. The user interacts with the system via a `Typer`-based CLI enhanced by `Rich` for colorful output. Configuration will be loaded from a global `~/.sg_agent/config.yaml` with local `.sg_agent.yaml` overrides parsed by `PyYAML`. All background events and daemon state will be logged cleanly via Python's standard `logging.handlers.RotatingFileHandler`.

## Libraries & Tools
| Library | Purpose | Why | Confidence | Source |
|---------|---------|-----|-----------|--------|
| `typer` | CLI Framework | Type-hint based, easy to write, intuitive interface. | HIGH | Verified via search: tiangolo.com |
| `rich` | Terminal Formatting | Colorful outputs, tables, and progress bars. Integrates well with Typer. | HIGH | Verified via search: tiangolo.com |
| `watchdog` | File Monitoring | Standard, cross-platform background continuous file listener. | HIGH | Verified via search: readthedocs.io |
| `pyyaml` | Configuration | Safe YAML parsing (`yaml.safe_load`) for easy-to-read config file structure. | HIGH | Verified via search: pyyaml.org |
| `logging` | Background Logging | Standard library, robust `RotatingFileHandler` support out of the box. | HIGH | Standard standard library |

## Patterns to Follow
- **CLI Commands as Typer Apps**: Use `@app.command()` for distinct subcommands like `start`, `stop`, `status`, and `logs`.
- **Global + Local Config Merging**: Load the global configuration dictionary first, then recursively update it with the local configuration file if present.
- **Daemon Backoff Iteration**: Use a simple loop for the daemon crash boundary, catching broad exceptions, logging them, incrementing a failure counter, and sleeping (`time.sleep()`) before restarting or exiting cleanly on the 3rd failure.

## Pitfalls to Avoid
- **Watchdog event bursts**: Modifying a file usually triggers multiple events. Prevention: debounce events or only react strictly to `FileCreatedEvent` / `FileModifiedEvent` on non-ignored directories.
- **Arbitrary YAML execution risk**: `yaml.load()` is vulnerable to arbitrary code execution if untrusted YAML is parsed. Prevention: strictly use `yaml.safe_load()`.
- **Zombie processes**: Daemon loop gets orphaned if signal is unhandled. Prevention: register `SIGTERM` and `SIGINT` handlers to cleanly shut down the daemon and observer.

## Key References
- Typer Documentation: https://typer.tiangolo.com/
- Watchdog Documentation: https://pythonhosted.org/watchdog/
- PyYAML Documentation: https://pyyaml.org/wiki/PyYAMLDocumentation

## Unverified Claims
None.

---
*Researched: 2026-03-06*
