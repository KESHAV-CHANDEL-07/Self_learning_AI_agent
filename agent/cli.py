import typer
import os
import signal
import sys
import subprocess
from pathlib import Path
from rich.console import Console

from agent.daemon import DaemonWatcher
from agent.config import load_config
from agent.logger import setup_logger

app = typer.Typer(help="Self-Learning AI Agent CLI")
console = Console()

PID_FILE = Path.home() / ".sg_agent" / "agent.pid"

def run_daemon_process():
    global_config_path = Path.home() / ".sg_agent" / "config.yaml"
    local_config_path = Path(".sg_agent.yaml")
    config = load_config(global_config_path, local_config_path)
    
    log_dir = Path.home() / ".sg_agent" / "logs"
    setup_logger(log_dir, config.get("log_level", "INFO"))
    
    watcher = DaemonWatcher(watch_dir=".", poll_interval=config.get("poll_interval", 5))
    watcher.start()

@app.command()
def start(daemon: bool = typer.Option(False, "--daemon", "-d", help="Run in background")):
    """Start the AI Agent daemon."""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            # Basic sanity check
            if sys.platform == "win32":
                output = subprocess.check_output(f'tasklist /FI "PID eq {pid}"', shell=True).decode()
                if str(pid) in output:
                    console.print(f"[bold yellow]Daemon is already running with PID {pid}[/]")
                    return
            else:
                os.kill(pid, 0)
                console.print(f"[bold yellow]Daemon is already running with PID {pid}[/]")
                return
        except Exception:
            pass
        PID_FILE.unlink()

    if daemon:
        console.print("[bold green]Starting daemon in background...[/]")
        flags = 0
        if sys.platform == "win32":
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            
        p = subprocess.Popen([sys.executable, "main.py", "start"], creationflags=flags)
        PID_FILE.write_text(str(p.pid))
        console.print(f"[green]Daemon started with PID {p.pid}[/]")
    else:
        console.print("[bold green]Starting daemon in foreground...[/]")
        PID_FILE.write_text(str(os.getpid()))
        try:
            run_daemon_process()
        finally:
            if PID_FILE.exists():
                PID_FILE.unlink()

@app.command()
def stop():
    """Stop the running AI Agent daemon."""
    if not PID_FILE.exists():
        console.print("[bold yellow]No daemon process found.[/]")
        return
        
    try:
        pid = int(PID_FILE.read_text().strip())
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        else:
            os.kill(pid, signal.SIGTERM)
        console.print(f"[bold green]Stopped daemon (PID {pid}).[/]")
        PID_FILE.unlink()
    except Exception:
        console.print("[bold red]Failed to stop daemon.[/]")
        PID_FILE.unlink()

@app.command()
def status():
    """Check the status of the AI Agent daemon."""
    if not PID_FILE.exists():
        console.print("[bold red]Agent is STOPPED.[/]")
        return
        
    try:
        pid = int(PID_FILE.read_text().strip())
        if sys.platform == "win32":
            output = subprocess.check_output(f'tasklist /FI "PID eq {pid}"', shell=True).decode()
            if str(pid) in output:
                console.print(f"[bold green]Agent is RUNNING (PID {pid}).[/]")
            else:
                console.print("[bold red]Agent is STOPPED (stale PID).[/]")
                PID_FILE.unlink()
        else:
            os.kill(pid, 0)
            console.print(f"[bold green]Agent is RUNNING (PID {pid}).[/]")
    except Exception:
        console.print("[bold red]Agent is STOPPED (stale PID file).[/]")
        if PID_FILE.exists():
            PID_FILE.unlink()

@app.command()
def logs(tail: int = typer.Option(20, help="Number of lines to show")):
    """View the daemon logs."""
    log_file = Path.home() / ".sg_agent" / "logs" / "agent.log"
    if not log_file.exists():
        console.print("[bold yellow]No log file found.[/]")
        return
        
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-tail:]:
                console.print(line.strip(), highlight=False)
    except Exception as e:
        console.print(f"[bold red]Error reading log: {e}[/]")

if __name__ == "__main__":
    app()
