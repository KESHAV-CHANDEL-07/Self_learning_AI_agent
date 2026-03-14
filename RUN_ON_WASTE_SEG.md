# 🚀 Run AI Agent on Waste_seg

To start the AI agent and begin sorting files in the `Waste_seg` project, follow these steps.

## 1. Environment Check
Ensure you are in the project root:
`c:\Users\kesha\OneDrive\Desktop\Self_Learning AI Agent`

Install dependencies if not already done:
```bash
pip install -r requirements.txt
```

## 2. Start File Sorting
Run the agent on the `TACO` subdirectory (where the data and scripts are located):

```bash
python main.py sort --episodes 50 --workspace "C:\Users\kesha\OneDrive\Desktop\Projects\ml-from-scratch\Waste_seg\TACO"
```

## 3. Run Workspace Cleanup
To remove empty folders from the project:

```bash
python main.py cleanup --workspace "C:\Users\kesha\OneDrive\Desktop\Projects\ml-from-scratch\Waste_seg\TACO"
```

## 4. Check Agent Accuracy
You can see what the agent has learned (its "intelligence") by running:

```bash
python main.py accuracy
```
This shows the "Confidence" (Q-value) the agent has for each file type. Higher numbers mean the agent is more certain about where a file belongs.

## 5. Using the Package-Aware PathResolver
If you want to move files while automatically updating all package imports, you can now use the CLI directly:

```bash
python main.py move "C:\Users\kesha\OneDrive\Desktop\Projects\ml-from-scratch\Waste_seg\TACO\quick_check.py" "core" --workspace "C:\Users\kesha\OneDrive\Desktop\Projects\ml-from-scratch\Waste_seg\TACO"
```

Alternatively, you can run a Python script:
```python
# Create a script (e.g., move_file.py) and run it:
from agent.action import ActionExecutor

workspace = r"C:\Users\kesha\OneDrive\Desktop\Projects\ml-from-scratch\Waste_seg\TACO"
executor = ActionExecutor(workspace)
executor.move_file(workspace + r"\quick_check.py", "core")
```

---
*Note: The agent will create a `.agent_cache.db` and a `.ropeproject` folder inside the workspace to track its internal state and refactoring history.*
