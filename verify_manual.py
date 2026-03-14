import os
import json
from agent.action import ActionExecutor

def verify():
    workspace = "demo_workspace_manual"
    os.makedirs(workspace, exist_ok=True)
    
    # 1. Create util
    utils_path = os.path.join(workspace, "utils.py")
    with open(utils_path, "w", encoding="utf-8") as f:
        f.write("def helper():\n    return 'Hello'\n")

    # 2. Create main
    main_path = os.path.join(workspace, "main.py")
    with open(main_path, "w", encoding="utf-8") as f:
        f.write("import utils\nprint(utils.helper())\n")

    # 3. Create config
    config_path = os.path.join(workspace, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump({"script": "utils.py"}, f)
        
    print("--- BEFORE ---")
    print("main.py:", open(main_path).read().strip())
    print("config.json:", open(config_path).read().strip())

    # 4. Move file
    executor = ActionExecutor(workspace)
    success = executor.move_file(utils_path, "code")
    print("\nMove successful:", success)

    # 5. Verify
    print("\n--- AFTER ---")
    print("main.py:", open(main_path).read().strip())
    print("config.json:", open(config_path).read().strip())

if __name__ == "__main__":
    verify()
