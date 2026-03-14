#!/usr/bin/env python
"""
run_on_repo.py — Classify and optionally sort every file in a repository
========================================================================
Usage::

    python run_on_repo.py <repo_url_or_path> [--report] [--sort] [--use-ai]

Flags:
    --report    Print classification reasoning per file
    --sort      Actually move files into category folders
    --use-ai    Enable Ollama LLM layer (Layer 3)

Zero external API calls.  Fully local.
"""

import argparse
import os
import shutil
import sys
import tempfile

from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

# Ensure project root is on sys.path so ``agent.*`` and ``utils.*`` resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.file_classifier import FileClassifier
from agent.path_filter import PathFilter

console = Console()

# ── helpers ───────────────────────────────────────────────────────────────

def _clone_repo(url: str) -> str:
    """Clone a git repo to a temp directory and return the path."""
    try:
        import git  # gitpython
    except ImportError:
        console.print("[bold red]gitpython is required. pip install gitpython[/]")
        sys.exit(1)

    dest = tempfile.mkdtemp(prefix="sg_repo_")
    console.print(f"[cyan]Cloning {url} → {dest}[/]")
    git.Repo.clone_from(url, dest)
    return dest


def _walk_files(root: str):
    """Yield all file paths under *root*, skipping hidden / VCS dirs."""
    path_filter = PathFilter()
    for dirpath, dirnames, filenames in os.walk(root):
        # prune hidden dirs, .git, __pycache__, node_modules, etc.
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".")
            and d not in {"__pycache__", "node_modules", ".git", ".venv", "venv"}
        ]
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            rel = os.path.relpath(fpath, root)
            if not path_filter.should_ignore(rel):
                yield fpath


def _sort_files(repo_path: str, results: list) -> dict:
    """Move files into category folders. Returns {moved, skipped, errors}."""
    stats = {"moved": 0, "skipped": 0, "errors": 0}

    for r in results:
        src = r["file_path"]
        cat = r.get("final_category", "misc")
        sub = r.get("final_subcategory")

        # Build destination folder
        if sub:
            dest_folder = os.path.join(repo_path, cat, sub)
        else:
            dest_folder = os.path.join(repo_path, cat)

        filename = os.path.basename(src)
        dest_path = os.path.join(dest_folder, filename)

        # Skip if file is already in the correct folder
        current_rel = os.path.relpath(src, repo_path)
        if sub:
            target_rel = os.path.join(cat, sub, filename)
        else:
            target_rel = os.path.join(cat, filename)

        if os.path.normpath(current_rel) == os.path.normpath(target_rel):
            stats["skipped"] += 1
            continue

        # Skip if destination already has a file with same name
        if os.path.exists(dest_path):
            console.print(f"  [yellow]⚠ Skipped (exists): {filename} → {cat}[/]")
            stats["skipped"] += 1
            continue

        try:
            os.makedirs(dest_folder, exist_ok=True)
            shutil.move(src, dest_path)
            console.print(f"  [green]✓ {current_rel} → {target_rel}[/]")
            stats["moved"] += 1
        except Exception as exc:
            console.print(f"  [red]✗ Failed: {filename} — {exc}[/]")
            stats["errors"] += 1

    return stats


# ── main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Classify (and optionally sort) every file in a repository using the 3-layer local classifier."
    )
    parser.add_argument(
        "repo",
        help="Path to a local directory or a GitHub URL to clone",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print classification reasoning per file",
    )
    parser.add_argument(
        "--sort",
        action="store_true",
        help="Actually move files into classified category folders",
    )
    parser.add_argument(
        "--use-ai",
        action="store_true",
        dest="use_ai",
        help="Enable Ollama LLM layer (Layer 3) when confidence is low",
    )
    args = parser.parse_args()

    # Resolve repo path
    repo_path = args.repo
    if repo_path.startswith("http://") or repo_path.startswith("https://"):
        repo_path = _clone_repo(repo_path)
    else:
        repo_path = os.path.abspath(repo_path)

    if not os.path.isdir(repo_path):
        console.print(f"[bold red]Not a directory: {repo_path}[/]")
        sys.exit(1)

    console.print(f"\n[bold green]Classifying files in:[/] {repo_path}\n")

    classifier = FileClassifier(use_llm=args.use_ai)

    # ── classify ─────────────────────────────────────────────────────────
    results = []

    for fpath in _walk_files(repo_path):
        result = classifier.classify(fpath, skip_cache=True)
        results.append(result)

    # ── report ───────────────────────────────────────────────────────────
    if args.report or args.sort:
        table = Table(title="File Classification Report", show_lines=True)
        table.add_column("File", style="cyan", max_width=50)
        table.add_column("Category", style="green")
        table.add_column("Confidence", style="magenta", justify="right")
        table.add_column("Reasoning", style="yellow", max_width=60)

        for r in results:
            rel = os.path.relpath(r["file_path"], repo_path)
            cat = r.get("final_category", "misc")
            sub = r.get("final_subcategory")
            if sub:
                cat = f"{cat}/{sub}"
            conf = f"{r.get('confidence', 0):.2f}"
            reasoning = r.get("reasoning", "")
            table.add_row(rel, cat, conf, reasoning)

        console.print(table)

    # ── sort ─────────────────────────────────────────────────────────────
    if args.sort:
        console.print(f"\n[bold yellow]⚠ This will move {len(results)} files into category folders.[/]")
        if Confirm.ask("[bold]Proceed with sorting?[/]", default=False):
            console.print("\n[bold]Sorting files...[/]\n")
            stats = _sort_files(repo_path, results)
            console.print(f"\n[bold green]Sort complete:[/]")
            console.print(f"  Moved:   [green]{stats['moved']}[/]")
            console.print(f"  Skipped: [yellow]{stats['skipped']}[/]")
            console.print(f"  Errors:  [red]{stats['errors']}[/]")
        else:
            console.print("[yellow]Sort cancelled.[/]")

    # ── summary ──────────────────────────────────────────────────────────
    console.print(f"\n[bold]Summary[/]")
    console.print(f"  Total files classified: [cyan]{len(results)}[/]")
    console.print(f"  External API calls:     [green]0[/]")

    # Category breakdown
    category_counts = {}
    for r in results:
        cat = r.get("final_category", "misc")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    if category_counts:
        summary_table = Table(title="Category Breakdown")
        summary_table.add_column("Category", style="cyan")
        summary_table.add_column("Count", style="green", justify="right")
        for cat, count in sorted(category_counts.items()):
            summary_table.add_row(cat, str(count))
        console.print(summary_table)

    console.print(f"\n[bold green]✓ Classification complete — 0 external API calls[/]\n")


if __name__ == "__main__":
    main()
