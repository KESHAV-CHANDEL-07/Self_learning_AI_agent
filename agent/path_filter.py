import logging
from pathlib import Path
from typing import List, Optional

from pathspec import PathSpec

logger = logging.getLogger("agent.path_filter")

DEFAULT_IGNORE_PATTERNS = [
    ".git",
    "__pycache__",
    "node_modules",
    ".env",
    "*.pyc",
    ".DS_Store",
    "*.egg-info",
    ".venv",
    "venv",
    ".agent_cache.db",
    ".ropeproject",
    "agent.log",
]


class PathFilter:
    """Combines default, config, and .gitignore patterns into a single filter."""

    def __init__(
        self,
        config_patterns: Optional[List[str]] = None,
        gitignore_path: Optional[Path] = None,
    ):
        """
        Initialize the PathFilter with combined patterns.

        Args:
            config_patterns: Additional ignore patterns from user config.
            gitignore_path: Path to a .gitignore file to include.
        """
        all_patterns = list(DEFAULT_IGNORE_PATTERNS)

        if config_patterns is not None:
            all_patterns.extend(config_patterns)

        if gitignore_path is not None and gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    gitignore_lines = [
                        line.strip()
                        for line in f
                        if line.strip() and not line.strip().startswith("#")
                    ]
                all_patterns.extend(gitignore_lines)
            except Exception as e:
                logger.warning(f"Failed to read .gitignore at {gitignore_path}: {e}")

        self._spec = PathSpec.from_lines("gitwildmatch", all_patterns)
        self._patterns = all_patterns
        logger.debug(f"PathFilter initialized with {len(all_patterns)} patterns")

    def should_ignore(self, path: str) -> bool:
        """
        Check if a path should be ignored.

        Args:
            path: The file or directory path to check.

        Returns:
            True if the path matches any ignore pattern.
        """
        return self._spec.match_file(path)

    def get_patterns(self) -> List[str]:
        """
        Return the combined list of active ignore patterns.

        Returns:
            List of all pattern strings currently active.
        """
        return list(self._patterns)
