import os
import shutil
from pathlib import Path
import pytest
import json

from agent.path_resolver import PathResolver

@pytest.fixture
def temp_workspace(tmp_path):
    # Create mock workspace
    ws = tmp_path / "workspace"
    ws.mkdir()
    
    # Create utils.py
    utils_code = "def add(a, b): return a + b\n"
    (ws / "utils.py").write_text(utils_code, encoding="utf-8")
    
    # Create main.py that imports utils
    main_code = "import utils\nfrom utils import add\nprint(utils.add(1, 2))\n"
    (ws / "main.py").write_text(main_code, encoding="utf-8")
    
    # Create config file referencing utils.py
    config_data = {"script": "utils.py"}
    (ws / "config.json").write_text(json.dumps(config_data), encoding="utf-8")
    
    return ws

def test_path_resolver_python_imports(temp_workspace):
    resolver = PathResolver(temp_workspace)
    
    # Simulate moving utils.py to code/utils.py
    code_dir = temp_workspace / "code"
    code_dir.mkdir()
    shutil.move(str(temp_workspace / "utils.py"), str(code_dir / "utils.py"))
    
    # Update references
    old_path = temp_workspace / "utils.py"
    new_path = code_dir / "utils.py"
    resolver.update_references(str(old_path), str(new_path))
    
    # Verify main.py
    main_content = (temp_workspace / "main.py").read_text(encoding="utf-8")
    assert "import code.utils" in main_content, "Import declaration failed to update"
    assert "from code.utils import add" in main_content, "From import failed to update"
    
def test_path_resolver_text_replacement(temp_workspace):
    resolver = PathResolver(temp_workspace)
    
    code_dir = temp_workspace / "code"
    code_dir.mkdir()
    shutil.move(str(temp_workspace / "utils.py"), str(code_dir / "utils.py"))
    
    # Update references
    old_path = temp_workspace / "utils.py"
    new_path = code_dir / "utils.py"
    resolver.update_references(str(old_path), str(new_path))
    
    # Verify config.json
    config_content = (temp_workspace / "config.json").read_text(encoding="utf-8")
    assert "code/utils.py" in config_content, "JSON config failed to update"

def test_verify_syntax(temp_workspace):
    resolver = PathResolver(temp_workspace)
    assert resolver.verify_syntax() is True

    # Intentionally ruin a file
    (temp_workspace / "bad.py").write_text("def broken(", encoding="utf-8")
    assert resolver.verify_syntax() is False
