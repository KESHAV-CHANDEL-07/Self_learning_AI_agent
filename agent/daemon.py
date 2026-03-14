import time
import signal
import logging
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from agent.path_filter import PathFilter
from agent.plugin_registry import PluginRegistry

logger = logging.getLogger("agent.daemon")

SHUTDOWN_TIMEOUT = 10


class WorkspaceHandler(FileSystemEventHandler):
    """Handles file system events with path filtering and plugin dispatch."""

    def __init__(self, path_filter: PathFilter, plugin_registry: PluginRegistry):
        """
        Initialize the handler.

        Args:
            path_filter: PathFilter instance for ignoring paths.
            plugin_registry: PluginRegistry instance for dispatching events.
        """
        super().__init__()
        self.path_filter = path_filter
        self.plugin_registry = plugin_registry

    def on_any_event(self, event):
        if event.is_directory or self.path_filter.should_ignore(event.src_path):
            return

        logger.info(f"File event: {event.event_type} at {event.src_path}")

        event_data = {
            "type": event.event_type,
            "path": event.src_path,
            "is_directory": event.is_directory,
        }
        # The event.src_path is the exact file. We need to tell the plugins 
        # what the top-level repo/workspace directory is.
        # since self.watch_dir and event.src_path might differ (nested files),
        # we can pass the top-level watch dir itself as the workspace, 
        # or compute the specific repo directory under watch_dir.
        # For a structure like ~/.sg_agent/workspaces/<repo>/<file>
        # we want to pass ~/.sg_agent/workspaces/<repo>
        from pathlib import Path
        src = Path(event.src_path)
        base = Path(self.plugin_registry.plugins_dir).parent / "workspaces" # A simple heuristic
        try:
            # find the immediate child of workspaces that contains this file
            rel_parts = src.relative_to(base).parts
            if rel_parts:
                workspace_path = base / rel_parts[0]
            else:
                workspace_path = base
        except ValueError:
            workspace_path = src.parent

        context = {"workspace": str(workspace_path)}

        try:
            self.plugin_registry.run_all(event_data, context)
        except Exception as e:
            logger.error(f"Plugin dispatch error: {e}")


class DaemonWatcher:
    """Watches a directory for file changes with graceful shutdown support."""

    def __init__(
        self,
        watch_dir: str,
        poll_interval: int = 5,
        path_filter: PathFilter = None,
        plugin_registry: PluginRegistry = None,
    ):
        """
        Initialize the DaemonWatcher.

        Args:
            watch_dir: Directory to watch for changes.
            poll_interval: Seconds between poll cycles.
            path_filter: PathFilter instance (created if None).
            plugin_registry: PluginRegistry instance (created if None).
        """
        self.watch_dir = watch_dir
        self.poll_interval = poll_interval
        self.observer = None
        self._shutdown_event = threading.Event()
        self.crash_count = 0
        self._errors: list = []
        self.path_filter = path_filter or PathFilter()
        self.plugin_registry = plugin_registry or PluginRegistry()

    @property
    def running(self) -> bool:
        """True if the daemon has not been signaled to shut down."""
        return not self._shutdown_event.is_set()

    def start(self):
        """Start the daemon watcher loop with auto-restart on crash."""
        self._shutdown_event.clear()

        # Register signal handlers for graceful shutdown (only in main thread)
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except ValueError:
            # Might happen if not run in main thread during tests
            pass

        # Discover plugins before starting
        self.plugin_registry.discover()

        while self.running and self.crash_count < 3:
            try:
                self.observer = Observer()
                event_handler = WorkspaceHandler(
                    self.path_filter, self.plugin_registry
                )
                self.observer.schedule(event_handler, self.watch_dir, recursive=True)
                self.observer.start()
                logger.info(
                    f"Started daemon watching {self.watch_dir} "
                    f"(polling: {self.poll_interval}s)"
                )

                while self.running:
                    time.sleep(self.poll_interval)

            except Exception as e:
                self.crash_count += 1
                self._errors.append(str(e))
                logger.error(f"Daemon crashed: {e}. Restart {self.crash_count}/3")
                if self.observer:
                    self.observer.stop()
                    self.observer.join()

                if self.crash_count < 3:
                    backoff = (2 ** self.crash_count) * 5
                    logger.info(f"Sleeping {backoff}s before restart...")
                    time.sleep(backoff)
                else:
                    logger.critical("Maximum crash limit reached. Exiting.")
                    self._shutdown_event.set()

        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()

    def _signal_handler(self, signum=None, frame=None):
        """Handle OS signals for graceful shutdown."""
        self.shutdown(signum)

    def shutdown(self, signum=None, frame=None):
        """
        Gracefully shut down the daemon with a timeout.

        Args:
            signum: Signal number that triggered shutdown (optional).
            frame: Stack frame (optional, unused).
        """
        logger.info(f"Shutdown signal received ({signum}). Stopping daemon...")
        self._shutdown_event.set()
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=SHUTDOWN_TIMEOUT)
            if self.observer.is_alive():
                logger.warning(
                    "Observer did not stop within timeout, forcing exit"
                )

    def get_errors(self) -> list:
        """Return the list of errors encountered during execution."""
        return list(self._errors)
