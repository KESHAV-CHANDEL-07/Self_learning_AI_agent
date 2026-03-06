import pytest
from pathlib import Path
import yaml
from agent.config import load_config, DEFAULT_CONFIG

@pytest.fixture
def temp_config_files(tmp_path):
    global_path = tmp_path / "global.yaml"
    local_path = tmp_path / "local.yaml"
    return global_path, local_path

def test_load_config_defaults(temp_config_files):
    global_path, local_path = temp_config_files
    config = load_config(global_path, local_path)
    assert config == DEFAULT_CONFIG

def test_load_config_global_only(temp_config_files):
    global_path, local_path = temp_config_files
    global_config = {"log_level": "DEBUG", "new_setting": "value1"}
    with open(global_path, "w") as f:
        yaml.safe_dump(global_config, f)
    
    config = load_config(global_path, local_path)
    assert config["log_level"] == "DEBUG"
    assert config["new_setting"] == "value1"
    assert config["poll_interval"] == 5

def test_load_config_local_overrides_global(temp_config_files):
    global_path, local_path = temp_config_files
    global_config = {"log_level": "DEBUG", "poll_interval": 10}
    with open(global_path, "w") as f:
        yaml.safe_dump(global_config, f)
    
    local_config = {"poll_interval": 20, "local_setting": "value2"}
    with open(local_path, "w") as f:
        yaml.safe_dump(local_config, f)
        
    config = load_config(global_path, local_path)
    assert config["log_level"] == "DEBUG"
    assert config["poll_interval"] == 20
    assert config["local_setting"] == "value2"

def test_load_config_malformed_yaml(temp_config_files, caplog):
    global_path, local_path = temp_config_files
    with open(global_path, "w") as f:
        f.write("invalid: yaml: format: []")
        
    config = load_config(global_path, local_path)
    assert config == DEFAULT_CONFIG
    assert "Failed to parse config file" in caplog.text
