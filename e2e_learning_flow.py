# e2e_learning_flow.py
"""End-to-end verification script for Phase 3 learning persistence."""

import os
import shutil
from tasks.file_sorting import run_file_sort_task
from agent.sqlite_dao import SQLiteDAO, DEFAULT_DB_PATH

def setup_workspace():
    workspace = os.path.expanduser("~/.sg_agent/workspaces/e2e_test")
    os.makedirs(workspace, exist_ok=True)
    # create some files
    with open(os.path.join(workspace, "test1.txt"), "w") as f:
        f.write("hello")
    with open(os.path.join(workspace, "test2.jpg"), "w") as f:
        f.write("image")
    return workspace

def teardown_workspace(workspace):
    shutil.rmtree(workspace, ignore_errors=True)

def main():
    print("--- Starting E2E Verification ---")
    
    # 1. Clear old DB if it exists
    if os.path.exists(DEFAULT_DB_PATH):
        os.remove(DEFAULT_DB_PATH)
        
    workspace = setup_workspace()
    
    try:
        # 2. Run file sorting task (this completes 10 episodes by default)
        run_file_sort_task(workspace_dir=workspace, episodes=2)
        
        # 3. Verify SQLite DB exists and contains Q-values
        assert os.path.exists(DEFAULT_DB_PATH), "DB file was not created!"
        
        # 4. Read DB manually 
        dao = SQLiteDAO()
        entries = dao.all_entries()
        assert len(entries) > 0, "No Q-values were saved to the database!"
        print(f"Success! Found {len(entries)} Q-value entries in the DB.")
        
        for state, action, q_value in entries:
            print(f"State: {state}, Action: {action}, Q: {q_value:.4f}")
            
        print("--- E2E Verification Passed ---")
    finally:
        teardown_workspace(workspace)

if __name__ == "__main__":
    main()
