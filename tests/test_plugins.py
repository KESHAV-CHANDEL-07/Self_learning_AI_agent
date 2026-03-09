# tests/test_plugins.py
"""Unit tests for the plugin wrappers.
"""

import sys
import os
import importlib.util
# Ensure plugins directory is on import path for test discovery
sys.path.append(os.path.expanduser('~/.sg_agent/plugins'))
import os

PLUGIN_DIR = os.path.expanduser("~/.sg_agent/plugins")

def load_plugin(module_name: str):
    path = os.path.join(PLUGIN_DIR, f"{module_name}.py")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_file_sorting_plugin_runs():
    plugin = load_plugin("file_sorting_plugin")
    assert hasattr(plugin, "run")
    # Run should not raise
    plugin.run({}, {})

def test_file_cleanup_plugin_runs():
    plugin = load_plugin("file_cleanup_plugin")
    assert hasattr(plugin, "run")
    plugin.run({}, {})
