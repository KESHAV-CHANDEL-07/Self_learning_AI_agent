import typer
import os
import signal
import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table

from agent.daemon import DaemonWatcher
from agent.config import load_config
from agent.logger import setup_logger
from agent.repo_manager import RepoManager
from agent.path_filter import PathFilter
from agent.plugin_registry import PluginRegistry

app = typer.Typer(help="Self-Learning AI Agent CLI")
console = Console()

PID_FILE = Path.home() / ".sg_agent" / "agent.pid"


def run_daemon_process():
    global_config_path = Path.home() / ".sg_agent" / "config.yaml"
    local_config_path = Path(".sg_agent.yaml")
    config = load_config(global_config_path, local_config_path)

    log_dir = Path.home() / ".sg_agent" / "logs"
    setup_logger(log_dir, config.get("log_level", "INFO"))

    # Phase 2: Create PathFilter and PluginRegistry from config
    ignore_patterns = config.get("ignore_patterns", [])
    plugins_dir = Path(config.get("plugins_dir", str(Path.home() / ".sg_agent" / "plugins")))
    workspaces_dir = Path(config.get("workspaces_dir", str(Path.home() / ".sg_agent" / "workspaces")))

    path_filter = PathFilter(config_patterns=ignore_patterns)
    plugin_registry = PluginRegistry(plugins_dir=plugins_dir)

    watcher = DaemonWatcher(
        watch_dir=str(workspaces_dir),
        poll_interval=config.get("poll_interval", 5),
        path_filter=path_filter,
        plugin_registry=plugin_registry,
    )
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

    # Show managed repos count
    try:
        manager = RepoManager()
        repos = manager.list_repos()
        console.print(f"[cyan]Managed repositories: {len(repos)}[/]")
    except Exception:
        pass


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


@app.command()
def add(url: str = typer.Argument(help="GitHub repo URL to clone")):
    """Add a remote GitHub repository to managed workspaces."""
    manager = RepoManager()
    result = manager.clone_or_pull(url)
    if result:
        console.print(f"[bold green]Repository added: {result}[/]")
    else:
        console.print("[bold red]Failed to add repository. Check logs for details.[/]")


@app.command()
def remove(name: str = typer.Argument(help="Repository name to remove")):
    """Remove a managed repository workspace."""
    manager = RepoManager()
    success = manager.remove_repo(name)
    if success:
        console.print(f"[bold green]Removed: {name}[/]")
    else:
        console.print(f"[bold red]Failed to remove: {name}[/]")
@app.command()
def sweep(name: str = typer.Argument(None, help="Specific repository name to sweep (optional)")):
    """Manually trigger all plugins (sorting, cleanup, etc.) on managed workspaces."""
    manager = RepoManager()
    repo_list = manager.list_repos()
    
    if not repo_list:
        console.print("[yellow]No managed repositories found to sweep.[/]")
        return
        
    global_config_path = Path.home() / ".sg_agent" / "config.yaml"
    local_config_path = Path(".sg_agent.yaml")
    config = load_config(global_config_path, local_config_path)
    plugins_dir = Path(config.get("plugins_dir", str(Path.home() / ".sg_agent" / "plugins")))
    plugin_registry = PluginRegistry(plugins_dir=plugins_dir)
    plugin_registry.discover()
    
    for repo in repo_list:
        if name and repo["name"] != name:
            continue
            
        repo_path = repo["path"]
        console.print(f"[bold green]Sweeping workspace:[/] {repo_path}")
        
        event_data = {
            "type": "manual_sweep",
            "path": repo_path,
            "is_directory": True,
        }
        context = {"workspace": repo_path}
        
        results = plugin_registry.run_all(event_data, context)
        for plugin, success in results.items():
            if success:
                console.print(f"  [green]✓ {plugin} succeeded[/]")
            else:
                console.print(f"  [red]✗ {plugin} failed[/]")
                
    console.print("[bold green]Sweep complete.[/]")


@app.command()
def repos():
    """List all managed repository workspaces."""
    manager = RepoManager()
    repo_list = manager.list_repos()
    if repo_list:
        table = Table(title="Managed Repositories")
        table.add_column("Name", style="cyan")
        table.add_column("Path", style="green")
        for repo in repo_list:
            table.add_row(repo["name"], repo["path"])
        console.print(table)
    else:
        console.print("[yellow]No managed repositories found.[/]")


@app.command()
def sort(
    workspace: str = typer.Option(None, "--workspace", "-w", help="Workspace directory"),
    episodes: int = typer.Option(10, "--episodes", "-e", help="Number of episodes to run"),
):
    """Run the file sorting task."""
    from tasks.file_sorting import run_file_sort_task
    run_file_sort_task(workspace_dir=workspace, episodes=episodes)


@app.command()
def cleanup(
    workspace: str = typer.Option(None, "--workspace", "-w", help="Workspace directory"),
):
    """Run the workspace cleanup task."""
    from tasks.file_cleanup import run_cleanup_task
    run_cleanup_task(workspace_dir=workspace)


@app.command()
def move(
    file: str = typer.Argument(..., help="Path to the file to move"),
    dest: str = typer.Argument(..., help="Destination folder name inside workspace"),
    workspace: str = typer.Option(None, "--workspace", "-w", help="Workspace root directory"),
):
    """Move a file and update all references (Package-Aware)."""
    from agent.action import ActionExecutor
    # If workspace is not provided, try to infer it from the file's parent
    if not workspace:
        workspace = str(Path(file).resolve().parent)
        console.print(f"[yellow]No workspace specified. Inferring from file location: {workspace}[/]")
    
    executor = ActionExecutor(workspace)
    success = executor.move_file(file, dest)
    if success:
        console.print(f"[bold green]Successfully moved {file} to {dest} and updated references.[/]")
    else:
        console.print(f"[bold red]Failed to move {file}. Check logs for details.[/]")


@app.command()
def accuracy():
    """Check the agent's learned knowledge (Accuracy)."""
    from agent.sqlite_dao import SQLiteDAO
    dao = SQLiteDAO()
    entries = dao.all_entries()
    
    if not entries:
        console.print("[yellow]Agent has not learned anything yet. Run some 'sort' tasks first![/]")
        return
        
    table = Table(title="Agent's Learned Intelligence (Accuracy)")
    table.add_column("File Type (State)", style="cyan")
    table.add_column("Best Folder (Action)", style="green")
    table.add_column("Confidence (Q-Value)", style="magenta")
    
    # Organize by state to find the best action for each
    best_actions = {}
    for state, action, q_val in entries:
        if state not in best_actions or q_val > best_actions[state][1]:
            best_actions[state] = (action, q_val)
            
    for state, (action, q_val) in sorted(best_actions.items()):
        table.add_row(state, action, f"{q_val:.2f}")
        
    console.print(table)


if __name__ == "__main__":
    app()
