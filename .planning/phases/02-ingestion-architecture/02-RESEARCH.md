# Phase 2: Ingestion & Architecture — Research

## Implementation Approach
Phase 2 adds three core capabilities: (1) repo ingestion via `GitPython` with clone/pull to managed workspaces, (2) path filtering using `pathspec` for `.gitignore`-style pattern matching combined with hardcoded defaults and config overrides, and (3) a plugin architecture using `importlib` to auto-discover single-file plugins from `~/.sg_agent/plugins/`. Graceful shutdown and robust error handling will be woven through all three subsystems.

## Libraries & Tools
| Library | Purpose | Why | Confidence | Source |
|---------|---------|-----|-----------|--------|
| `gitpython` (3.1.46) | Clone & manage repos | `Repo.clone_from(url, path)` for cloning, `repo.remotes.origin.pull()` for updates. Mature, well-documented. | HIGH | [GitPython docs](https://gitpython.readthedocs.io/en/stable/tutorial.html) |
| `pathspec` | `.gitignore`-style filtering | `PathSpec.from_lines('gitignore', patterns)` + `spec.match_file(path)`. Pure Python, lightweight. | HIGH | [GitHub: cpburnz/python-pathspec](https://github.com/cpburnz/python-pathspec) |
| `importlib` | Plugin auto-discovery | `importlib.util.spec_from_file_location()` + `loader.exec_module()`. Standard library, zero dependencies. | HIGH | Python stdlib docs |
| `signal` | Graceful shutdown | `signal.signal(SIGTERM, handler)` for intercepting termination. Already used in `daemon.py`. | HIGH | Python stdlib |

## Patterns to Follow
- **Repository Manager as a standalone module**: Keep all Git operations in `agent/repo_manager.py`, isolated from the daemon or CLI. This preserves testability and separation of concerns.
- **PathFilter as a composable utility**: `agent/path_filter.py` combines hardcoded defaults + global config + local config + `.gitignore` into one `PathSpec` object. Expose a single `should_ignore(path) -> bool` function.
- **Plugin interface via module-level constants**: Each plugin must export `PLUGIN_NAME: str`, `PLUGIN_VERSION: str`, and a `run(event: dict, context: dict) -> None` function. Auto-discovered by scanning `~/.sg_agent/plugins/*.py` at daemon startup.
- **Graceful shutdown with timeout**: Set a `threading.Event` as the shutdown flag. In the shutdown handler, set the event and `join(timeout=10)` on worker threads. If threads don't finish, force exit.
- **Retry with backoff for clone failures**: Use a simple retry loop (3 attempts, 5s delay) matching the existing daemon backoff pattern in `daemon.py`.

## Pitfalls to Avoid
- **GitPython requires system `git`**: `GitPython` shells out to `git`. If `git` is not installed, `Repo.clone_from()` will throw `GitCommandNotFound`. Prevention: check for `git` availability on startup with `git.Git().version_info` and surface a clear error.
- **Pathspec doesn't auto-read `.gitignore` per-directory**: Git's real ignore logic is hierarchical (each subdirectory can have its own `.gitignore`). Prevention: for V1, only read the root `.gitignore`. Document this as a known limitation.
- **Plugin import errors crash the daemon**: A bad plugin file (syntax error, missing function) can kill the whole daemon. Prevention: wrap each plugin import in `try/except`, log the error, and skip that plugin.
- **Permission errors on Windows**: File locking on Windows can cause `PermissionError` during cleanup or file operations. Prevention: catch `PermissionError` specifically, log it, and skip the file.

## Key References
- GitPython Tutorial: https://gitpython.readthedocs.io/en/stable/tutorial.html
- pathspec GitHub: https://github.com/cpburnz/python-pathspec
- Python importlib docs: https://docs.python.org/3/library/importlib.html

## Unverified Claims
None — all libraries and APIs verified via official documentation.

---
*Researched: 2026-03-06*
