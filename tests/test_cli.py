import pytest
from pathlib import Path
from typer.testing import CliRunner
from agent.cli import app, PID_FILE

runner = CliRunner()

def test_status_stopped():
    if PID_FILE.exists():
        PID_FILE.unlink()
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "Agent is STOPPED" in result.stdout

def test_logs_no_file(monkeypatch, tmp_path):
    def mock_home():
        return tmp_path
    monkeypatch.setattr(Path, "home", mock_home)
    result = runner.invoke(app, ["logs"])
    assert result.exit_code == 0
    assert "No log file found" in result.stdout

def test_stop_no_pid():
    if PID_FILE.exists():
        PID_FILE.unlink()
    result = runner.invoke(app, ["stop"])
    assert result.exit_code == 0
    assert "No daemon process found" in result.stdout
