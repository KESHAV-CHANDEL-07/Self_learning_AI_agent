import os
import sqlite3
import pathlib
from typing import Dict, List, Set, Optional, Tuple
from utils.logger import get_logger

logger = get_logger("PackageManager")

class PackageManager:
    def __init__(self, workspace_dir: str, db_path: str = ".agent_cache.db"):
        self.workspace_dir = pathlib.Path(workspace_dir).resolve()
        self.db_path = os.path.join(workspace_dir, db_path)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS package_map (
                module_name TEXT PRIMARY KEY,
                file_path TEXT,
                package_root TEXT
            )
        """)
        conn.commit()
        conn.close()

    def discover_packages(self) -> List[pathlib.Path]:
        """Finds all package roots (directories with __init__.py or containing build configs)."""
        roots = []
        for path in self.workspace_dir.rglob(""):
            if path.is_dir():
                if (path / "pyproject.toml").exists() or (path / "setup.py").exists() or (path / "setup.cfg").exists():
                    roots.append(path)
                elif (path / "__init__.py").exists():
                    # Check if it's a top-level package or part of one
                    if not (path.parent / "__init__.py").exists():
                        roots.append(path)
        return roots

    def build_module_map(self):
        """Builds the full module-to-file mapping for all discovered packages."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing map for full rebuild (can be optimized later to incremental)
        cursor.execute("DELETE FROM package_map")
        
        for root in self.discover_packages():
            for py_file in root.rglob("*.py"):
                if "__pycache__" in py_file.parts or "venv" in py_file.parts or ".venv" in py_file.parts:
                    continue
                
                module_name = self.get_module_name(py_file, root)
                if module_name:
                    cursor.execute(
                        "INSERT OR REPLACE INTO package_map (module_name, file_path, package_root) VALUES (?, ?, ?)",
                        (module_name, str(py_file.relative_to(self.workspace_dir)).replace("\\", "/"), str(root.relative_to(self.workspace_dir)).replace("\\", "/"))
                    )
        
        conn.commit()
        conn.close()
        logger.info("Module map rebuilt successfully.")

    def get_module_name(self, file_path: pathlib.Path, package_root: pathlib.Path) -> str:
        """Converts a file path to a module name relative to the package root."""
        try:
            rel_path = file_path.relative_to(package_root.parent)
            if rel_path.name == "__init__.py":
                parts = rel_path.parent.parts
            else:
                parts = list(rel_path.parent.parts) + [rel_path.stem]
            return ".".join(parts)
        except Exception:
            return ""

    def get_file_path(self, module_name: str) -> Optional[str]:
        """Returns the file path for a given module name from the cache."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM package_map WHERE module_name = ?", (module_name,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def update_entry(self, old_path: str, new_path: str):
        """Updates the mapping after a file move."""
        # Convert strings to Paths relative to workspace
        old_rel = pathlib.Path(old_path).relative_to(self.workspace_dir) if pathlib.Path(old_path).is_absolute() else pathlib.Path(old_path)
        new_rel = pathlib.Path(new_path).relative_to(self.workspace_dir) if pathlib.Path(new_path).is_absolute() else pathlib.Path(new_path)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find the entry by old path
        cursor.execute("SELECT module_name, package_root FROM package_map WHERE file_path = ?", (str(old_rel).replace("\\", "/"),))
        row = cursor.fetchone()
        if row:
            module_name, package_root = row
            # Calculate new module name if it moved within the same package or to a different one
            # For simplicity, we assume the user intends to keep the package structure or we rebuild after significant moves
            # But here we just update the file_path
            cursor.execute(
                "UPDATE package_map SET file_path = ? WHERE file_path = ?",
                (str(new_rel).replace("\\", "/"), str(old_rel).replace("\\", "/"))
            )
            
        conn.commit()
        conn.close()
