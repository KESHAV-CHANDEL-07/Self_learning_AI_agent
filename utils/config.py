import os

# Base directory for the agent's operations
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(BASE_DIR, "demo_workspace")

# Logging Configuration
LOG_FILE = os.path.join(BASE_DIR, "agent.log")
LOG_LEVEL = "INFO"

# RL Agent Configuration
LEARNING_RATE = 1.0  # Increased for immediate 1-shot learning
DISCOUNT_FACTOR = 0.0  # Decreased since actions are independent and lack delayed rewards
EXPLORATION_RATE = 0.01  # Lowered so it prefers exploiting known correct actions
EXPLORATION_DECAY = 0.99
MIN_EXPLORATION_RATE = 0.00  # Allows agent to stop exploring completely after training

# Task specific config for file sorting — new 3-layer classification categories
SUPPORTED_FILE_TYPES = {
    "code":           [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"],
    "code/frontend":  [".html", ".css", ".jsx", ".tsx", ".vue", ".scss"],
    "code/api":       [],   # determined by content analysis, not extension
    "code/auth":      [],   # determined by content analysis
    "code/ml":        [],   # determined by content analysis
    "config":         [".yaml", ".yml", ".json", ".toml", ".env", ".cfg", ".ini"],
    "docs":           [".md", ".rst", ".txt", ".pdf"],
    "images":         [".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".webp"],
    "data":           [".csv", ".xlsx", ".parquet", ".jsonl"],
    "database":       [".db", ".sqlite", ".sql"],
    "models":         [".pt", ".pth", ".pkl", ".h5", ".onnx"],
    "notebooks":      [".ipynb"],
    "tests":          [],   # determined by content/name analysis
    "scripts":        [".sh", ".bat", ".ps1"],
    "misc":           [],
}

# Rewards for reinforcement learning
REWARDS = {
    "successful_move": 10,
    "failed_move": -5,
    "invalid_action": -1,
    "already_organized": -1
}
