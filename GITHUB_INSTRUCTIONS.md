# 🌐 Running the AI Agent on GitHub Repositories

This guide explains how to use the AI Agent to manage, sort, and refactor any public GitHub repository.

## 🚀 Quick Start

To execute the agent on a new GitHub URL, follow these steps:

### 1. Add the Repository
Use the `add` command to clone the repository into the agent's managed workspace.
```bash
python main.py add https://github.com/USER/REPO_NAME.git
```
*The repository will be cloned to `~/.sg_agent/workspaces/REPO_NAME`.*

### 2. Verify Status
Check if the repository was added correctly and view the managed workspaces.
```bash
python main.py repos
```

### 3. Trigger a Manual Sweep (Sorting & Cleanup)
You can trigger all active plugins (like file sorting and directory cleanup) on the new repository:
```bash
python main.py sweep REPO_NAME
```

---

## 🛠️ Advanced Commands

### 🔍 Intelligence & Learning
If you want the agent to learn from the repository's structure (Q-Learning):
```bash
python main.py sort --workspace ~/.sg_agent/workspaces/REPO_NAME --episodes 100
```

### 🧹 Workspace Cleanup
Remove empty directories after reorganization:
```bash
python main.py cleanup --workspace ~/.sg_agent/workspaces/REPO_NAME
```

### 📦 Package-Aware Moving
Move a file and automatically update all its imports across the entire repository:
```bash
python main.py move path/to/file.py destination_folder --workspace ~/.sg_agent/workspaces/REPO_NAME
```

---

## 📊 Monitoring

- **Check Logs**: `python main.py logs --tail 50`
- **Check Accuracy**: `python main.py accuracy` (See what patterns the agent has learned!)
- **Daemon Status**: `python main.py status`

> [!TIP]
> You can run the agent in the background by starting it as a daemon:
> `python main.py start --daemon`
