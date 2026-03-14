# agent/sqlite_dao.py
"""SQLite Data Access Object for Q‑table persistence and classification cache.

Provides a thin wrapper around a SQLite database that stores state-action
Q‑values for the reinforcement‑learning agent **and** file classification
results from the 3-layer classifier pipeline.  The DAO is thread‑safe
using a simple ``threading.Lock`` because the daemon may invoke the
agent from multiple threads.
"""

import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional

DEFAULT_DB_PATH = os.path.expanduser("~/.sg_agent/data/learning.db")

class SQLiteDAO:
    """Singleton‑style DAO for Q‑table storage and classification cache.

    The table schemas are:
    ```sql
    CREATE TABLE IF NOT EXISTS q_table (
        state TEXT NOT NULL,
        action TEXT NOT NULL,
        q_value REAL NOT NULL,
        PRIMARY KEY (state, action)
    );

    CREATE TABLE IF NOT EXISTS classifications (
        file_path TEXT NOT NULL PRIMARY KEY,
        file_hash TEXT NOT NULL,
        pattern_category TEXT,
        ast_category TEXT,
        llm_category TEXT,
        final_category TEXT NOT NULL,
        confidence REAL NOT NULL,
        decided_at TEXT NOT NULL
    );
    ```
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = DEFAULT_DB_PATH):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SQLiteDAO, cls).__new__(cls)
                    cls._instance._init_db(db_path)
        return cls._instance

    def _init_db(self, db_path: str) -> None:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._db_path = db_path
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS q_table (
                state TEXT NOT NULL,
                action TEXT NOT NULL,
                q_value REAL NOT NULL,
                PRIMARY KEY (state, action)
            );
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS classifications (
                file_path TEXT NOT NULL PRIMARY KEY,
                file_hash TEXT NOT NULL,
                pattern_category TEXT,
                ast_category TEXT,
                llm_category TEXT,
                final_category TEXT NOT NULL,
                confidence REAL NOT NULL,
                decided_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()
        self._db_lock = threading.RLock()

    # ── Q-table methods ──────────────────────────────────────────────────

    def get_q(self, state: str, action: str) -> Optional[float]:
        """Return the stored Q‑value for *state*/*action* or ``None``.
        """
        with self._db_lock:
            cur = self._conn.execute(
                "SELECT q_value FROM q_table WHERE state = ? AND action = ?",
                (state, action),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def set_q(self, state: str, action: str, q_value: float) -> None:
        """Insert or replace a Q‑value.
        """
        with self._db_lock:
            self._conn.execute(
                "REPLACE INTO q_table (state, action, q_value) VALUES (?, ?, ?)",
                (state, action, q_value),
            )
            self._conn.commit()

    def increment_q(self, state: str, action: str, delta: float) -> None:
        """Add *delta* to the existing Q‑value, creating it if missing.
        """
        with self._db_lock:
            current = self.get_q(state, action)
            new_val = (current or 0.0) + delta
            self.set_q(state, action, new_val)

    def all_entries(self) -> Tuple[Tuple[str, str, float], ...]:
        """Return all ``(state, action, q_value)`` rows.
        """
        with self._db_lock:
            cur = self._conn.execute("SELECT state, action, q_value FROM q_table")
            return tuple(cur.fetchall())

    # ── Classification cache methods ─────────────────────────────────────

    def save_classification(
        self,
        file_path: str,
        file_hash: str,
        pattern_category: Optional[str],
        ast_category: Optional[str],
        llm_category: Optional[str],
        final_category: str,
        confidence: float,
    ) -> None:
        """Insert or replace a classification result."""
        with self._db_lock:
            self._conn.execute(
                """REPLACE INTO classifications
                   (file_path, file_hash, pattern_category, ast_category,
                    llm_category, final_category, confidence, decided_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    file_path,
                    file_hash,
                    pattern_category,
                    ast_category,
                    llm_category,
                    final_category,
                    confidence,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            self._conn.commit()

    def get_classification(self, file_path: str) -> Optional[Dict]:
        """Return the cached classification for *file_path* or ``None``."""
        with self._db_lock:
            cur = self._conn.execute(
                "SELECT * FROM classifications WHERE file_path = ?",
                (file_path,),
            )
            row = cur.fetchone()
            return self._row_to_classification(cur, row) if row else None

    def get_classification_by_hash(self, file_hash: str) -> Optional[Dict]:
        """Return a cached classification matching *file_hash* or ``None``."""
        if not file_hash:
            return None
        with self._db_lock:
            cur = self._conn.execute(
                "SELECT * FROM classifications WHERE file_hash = ?",
                (file_hash,),
            )
            row = cur.fetchone()
            return self._row_to_classification(cur, row) if row else None

    @staticmethod
    def _row_to_classification(cursor, row) -> Dict:
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, row))

    # ── lifecycle ────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the underlying SQLite connection.
        """
        with self._db_lock:
            self._conn.close()
            SQLiteDAO._instance = None

