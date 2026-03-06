import logging
import yaml
from pathlib import Path
from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    "log_level": "INFO",
    "poll_interval": 5,
}

def load_config(global_path: Path, local_path: Path) -> Dict[str, Any]:
    """
    Load configuration from global and local files, falling back to defaults.
    Local configuration overrides global configuration.
    """
    config = DEFAULT_CONFIG.copy()

    for path in [global_path, local_path]:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f)
                    if isinstance(file_config, dict):
                        config.update(file_config)
            except yaml.YAMLError as e:
                logging.warning(f"Failed to parse config file at {path}: {e}")
            except Exception as e:
                logging.warning(f"Error reading config file at {path}: {e}")

    return config
