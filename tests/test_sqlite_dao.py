# tests/test_sqlite_dao.py
"""Unit tests for the SQLiteDAO persistence layer.
"""

import os
import shutil
import tempfile
from agent.sqlite_dao import SQLiteDAO, DEFAULT_DB_PATH

def test_set_and_get_q_value():
    # Use a temporary directory for isolation
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "learning.db")
    dao = SQLiteDAO(db_path)
    dao.set_q("state1", "actionA", 1.23)
    assert dao.get_q("state1", "actionA") == 1.23
    dao.close()
    shutil.rmtree(temp_dir)

def test_increment_q_value():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "learning.db")
    dao = SQLiteDAO(db_path)
    # Increment when not present should start from 0
    dao.increment_q("state2", "actionB", 0.5)
    assert dao.get_q("state2", "actionB") == 0.5
    # Increment again
    dao.increment_q("state2", "actionB", 0.7)
    assert dao.get_q("state2", "actionB") == 1.2
    dao.close()
    shutil.rmtree(temp_dir)
