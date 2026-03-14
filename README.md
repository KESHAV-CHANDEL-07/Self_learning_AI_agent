# 🤖 Self-Learning AI Agent for Task Automation

An autonomous AI agent designed to reorganize codebases and automate file system tasks using a **perception-decision-action pipeline**. 

This agent features a sophisticated **Package-Aware PathResolver** that handles Python refactoring (imports, relative paths, and config updates) with extreme precision using `rope` and `libcst`.

---

## 🚀 Key Features

*   **Intelligent File Organization**: Uses Q-learning to categorize and move files based on learned patterns.
*   **Package-Aware PathResolver**: Automatically updates Python imports (absolute & relative) when modules are moved.
*   **Package Structure Mapping**: Tracks your project's module hierarchy in a local SQLite database (`.agent_cache.db`).
*   **Transactional Safety**: Verifies syntax and package integrity after reorganization with automatic fallback logging.
*   **Modern CLI**: Beautifully formatted terminal output using `rich`.

---

## 🛠️ Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/KESHAV-CHANDEL-07/Self_learning_AI_agent.git
    cd Self_learning_AI_agent
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

---

## 📖 Usage Instructions

### 1. Basic File Sorting (Learning Mode)
Organize a messy workspace while the agent learns the best categorization strategy.
```bash
python main.py sort --episodes 50 --workspace ./demo_workspace
```

### 3. Running on GitHub Repositories
The agent can manage and reorganize any public GitHub repository. Simply add the URL and trigger a sweep.
**[View the GitHub Execution Guide →](file:///c:/Users/kesha/OneDrive/Desktop/Self_Learning%20AI%20Agent/GITHUB_INSTRUCTIONS.md)**

### 4. Workspace Cleanup

### 3. Using PathResolver on Any Codebase
The agent's `PathResolver` can be used to reorganize any existing Python project without breaking imports.

#### Initializing the Module Map
To let the agent understand a new project (e.g., `Waste_seg`), first build the package map:
```python
from agent.package_manager import PackageManager
mgr = PackageManager(r"C:\path\to\your\project")
mgr.build_module_map()
```

#### Moving Files Safely
Trigger the `ActionExecutor` to move a file and update all its references across the package:
```python
from agent.action import ActionExecutor
executor = ActionExecutor(r"C:\path\to\your\project")
executor.move_file(r"C:\path\to\your\project\utils.py", "core/utils")
```

---

## 🏗️ System Architecture

*   **`agent/perception.py`**: Scans the workspace and identifies file types/states.
*   **`agent/decision.py`**: Q-learning engine choosing actions based on epsilon-greedy policy.
*   **`agent/action.py`**: Executes moves and triggers the PathResolver.
*   **`agent/path_resolver.py`**: The refactoring engine using `rope` to update package imports.
*   **`agent/package_manager.py`**: Manages the SQLite-based module-to-file mapping.
*   **`agent/memory.py`**: Handles persistence for the learned Q-table.

---

## 🧪 Verification & Testing

Run the automated test suite to verify the agent's logic and PathResolver precision:
```bash
python -m pytest tests/
```

To run a manual end-to-end verification of the PathResolver:
```bash
python verify_manual.py
```

---

## 📝 Configuration
- **`q_table.json`**: Stores the learned intelligence of the agent.
- **`.agent_cache.db`**: SQLite database created within target workspaces to track module paths.
- **`requirements.txt`**: List of external libraries (`libcst`, `rope`, `rich`, etc.).
