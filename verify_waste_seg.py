import os
import sys
from pathlib import Path

# Add current workspace to path so we can import the agent modules
sys.path.append(os.getcwd())

from agent.action import ActionExecutor
from agent.path_resolver import PathResolver

def test_on_waste_seg():
    waste_seg_path = r"C:\Users\kesha\OneDrive\Desktop\Projects\ml-from-scratch\Waste_seg\TACO"
    if not os.path.exists(waste_seg_path):
        print(f"Path not found: {waste_seg_path}")
        return

    print(f"Testing on: {waste_seg_path}")
    executor = ActionExecutor(waste_seg_path)
    
    # We'll try to move one of the scripts into a 'scripts' subdirectory
    old_file = os.path.join(waste_seg_path, "quick_check.py")
    if not os.path.exists(old_file):
        # Fallback to another file if quick_check.py isn't there
        old_file = os.path.join(waste_seg_path, "download.py")

    print(f"Moving {os.path.basename(old_file)} to 'scripts' folder...")
    
    # Ensure scripts folder exists
    os.makedirs(os.path.join(waste_seg_path, "scripts"), exist_ok=True)
    
    success = executor.move_file(old_file, "scripts")
    
    if success:
        print("Move and reference update SUCCESSFUL.")
    else:
        print("Move and reference update FAILED.")

if __name__ == "__main__":
    test_on_waste_seg()
