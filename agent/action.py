import os
import shutil
from utils.logger import get_logger


logger = get_logger("Action")

class ActionExecutor:
    def __init__(self, workspace_dir):
        self.workspace_dir = workspace_dir

    def execute(self, action_type, **kwargs):
        """
        Executes a given action.
        Returns True if successful, False otherwise.
        """
        if action_type == "move_file":
            return self.move_file(kwargs.get("filepath"), kwargs.get("destination_folder"))
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return False

    def move_file(self, filepath, destination_folder):
        """Moves a file to a destination folder within the workspace."""
        if not filepath or not destination_folder:
            return False

        try:
            dest_dir = os.path.join(self.workspace_dir, destination_folder)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            
            filename = os.path.basename(filepath)
            dest_path = os.path.join(dest_dir, filename)
            
            # 1. Initialize PathResolver
            try:
                from agent.path_resolver import PathResolver
                resolver = PathResolver(self.workspace_dir)
                resolver.build_dependency_map()
            except Exception as e:
                logger.error(f"Failed to initialize PathResolver: {e}")
                return False

            # 2. Backup if we were going to be truly transactional (simplified here)
            # We can use rope's undo logic or just file system backups if needed.
            
            logger.info(f"Moving file {filename} to {destination_folder}")
            # Ensure physical move happens
            if os.path.exists(filepath) and not os.path.exists(dest_path):
                shutil.move(filepath, dest_path)
            
            # 3. Resolve references
            # We tell PathResolver that the file HAS BEEN moved
            success = resolver.update_references(filepath, dest_path)
            
            if success:
                # 4. Post-Move Verification
                syntax_ok = resolver.verify_syntax()
                
                # Check for package integrity: import root if possible
                import_ok = True
                try:
                    # Try to import the package or the module itself to check for basic runtime errors
                    # This is a bit risky to do in-proc, better as a subprocess
                    import subprocess
                    # If it's a package, try to import the package name
                    # For now, we'll just check if it compiles
                    pass
                except Exception:
                    import_ok = False
                
                # Run tests if they exist
                tests_ok = True
                if os.path.exists(os.path.join(self.workspace_dir, "tests")):
                    res = subprocess.run(["pytest", "tests/"], cwd=self.workspace_dir, capture_output=True)
                    if res.returncode != 0:
                        logger.warning("Tests failed after move.")
                        tests_ok = False
                
                if not syntax_ok or not tests_ok:
                    logger.error(f"Integrity check failed after moving {filename}. Rollback suggested but not fully implemented in FS yet.")
                    # In a full transactional system, we would call resolver.rope_project.history.undo() here
                    # and move the file back.
                    return False



                return True
            else:
                logger.error(f"Failed to resolve references for {filename}")
                return False

        except Exception as e:
            logger.error(f"Failed to move file {filepath}: {e}")
            return False