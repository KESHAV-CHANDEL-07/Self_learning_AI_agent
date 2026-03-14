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

# Task specific config for file sorting
SUPPORTED_FILE_TYPES = {
    "images": [".jpg", ".png", ".jpeg", ".gif", ".svg", ".webp"],
    "documents": [".pdf", ".docx", ".txt", ".xlsx", ".csv", ".pptx"],
    "archives": [".zip", ".tar.gz", ".rar", ".7z"],
    "code": [".py", ".js", ".html", ".css", ".md", ".json", ".ts", ".go"],
    "audio": [".mp3", ".wav", ".flac", ".ogg"],
    "video": [".mp4", ".mkv", ".avi", ".mov"]
}

# Rewards for reinforcement learning
REWARDS = {
    "successful_move": 10,
    "failed_move": -5,
    "invalid_action": -1,
    "already_organized": -1
}
