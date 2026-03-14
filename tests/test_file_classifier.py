"""Tests for agent.file_classifier — Combination layer."""

import os
import tempfile
import textwrap
import shutil
import pytest
from unittest.mock import patch, MagicMock

from agent.file_classifier import FileClassifier, WEIGHT_PATTERN, WEIGHT_AST, WEIGHT_LLM
from agent.sqlite_dao import SQLiteDAO


@pytest.fixture
def temp_db():
    """Provide a fresh SQLiteDAO per test (no singleton)."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_learning.db")
    # Reset singleton
    SQLiteDAO._instance = None
    dao = SQLiteDAO(db_path)
    yield dao
    dao.close()
    shutil.rmtree(temp_dir)


@pytest.fixture
def classifier(temp_db):
    return FileClassifier(use_llm=False, dao=temp_db)


@pytest.fixture
def classifier_with_llm(temp_db):
    return FileClassifier(use_llm=True, dao=temp_db)


def _write_temp(content: str, suffix: str = ".py", name: str = None) -> str:
    if name:
        temp_dir = tempfile.mkdtemp()
        path = os.path.join(temp_dir, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(textwrap.dedent(content))
        return path
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(textwrap.dedent(content))
    return path


# ── Weight combination tests ─────────────────────────────────────────────

class TestWeightCombination:
    def test_weights_sum_to_one(self):
        assert WEIGHT_PATTERN + WEIGHT_AST + WEIGHT_LLM == pytest.approx(1.0)

    def test_pattern_30_ast_50(self):
        assert WEIGHT_PATTERN == pytest.approx(0.30)
        assert WEIGHT_AST == pytest.approx(0.50)
        assert WEIGHT_LLM == pytest.approx(0.20)


# ── Layer agreement tests ────────────────────────────────────────────────

class TestLayerAgreement:
    def test_both_layers_agree(self, classifier):
        """When L1 + L2 agree, the result should use that category."""
        code = """\
        import pytest

        def test_something():
            assert True
        """
        path = _write_temp(code, name="test_example.py")
        result = classifier.classify(path, skip_cache=True)
        assert result["final_category"] == "tests"
        shutil.rmtree(os.path.dirname(path))

    def test_ast_wins_on_disagreement(self, classifier):
        """When L1 and L2 disagree (without L3), AST wins (higher weight)."""
        # Name says 'config' but code imports flask → L1=config, L2=api
        code = """\
        from flask import Flask
        app = Flask(__name__)

        @app.route("/health")
        def health():
            return "ok"
        """
        path = _write_temp(code, name="config_server.py")
        result = classifier.classify(path, skip_cache=True)
        # AST should detect flask → code/api
        assert result["final_category"] == "code/api"
        shutil.rmtree(os.path.dirname(path))


# ── Fallback when Ollama missing ─────────────────────────────────────────

class TestOllamaFallback:
    def test_graceful_skip(self, classifier_with_llm):
        """Classifier should work even when Ollama is not installed."""
        code = "x = 1\n"
        path = _write_temp(code)
        # This should not crash
        result = classifier_with_llm.classify(path, skip_cache=True)
        assert "final_category" in result
        assert result["confidence"] > 0
        os.unlink(path)


# ── Cache tests ──────────────────────────────────────────────────────────

class TestCache:
    def test_cache_miss_then_hit(self, classifier, temp_db):
        """Second classify should hit cache."""
        code = "import pytest\n\ndef test_foo():\n    pass\n"
        path = _write_temp(code, name="test_cached.py")

        # First call — cache miss
        result1 = classifier.classify(path)
        assert result1["final_category"] is not None

        # Check DB
        cached = temp_db.get_classification(path)
        assert cached is not None
        assert cached["final_category"] == result1["final_category"]

        shutil.rmtree(os.path.dirname(path))


# ── Confidence boost tests ───────────────────────────────────────────────

class TestConfidenceBoost:
    def test_clear_test_file_high_confidence(self, classifier):
        """A clearly test file should get high confidence."""
        code = """\
        import pytest

        class TestAuth:
            def test_login(self):
                assert True
        """
        path = _write_temp(code, name="test_auth.py")
        result = classifier.classify(path, skip_cache=True)
        assert result["final_category"] == "tests"
        # L1 says tests, L2 says tests → should agree and boost
        assert result["confidence"] >= 0.7
        shutil.rmtree(os.path.dirname(path))


# ── Reasoning output tests ───────────────────────────────────────────────

class TestReasoning:
    def test_reasoning_populated(self, classifier):
        path = _write_temp("x = 1\n")
        result = classifier.classify(path, skip_cache=True)
        assert "reasoning" in result
        assert len(result["reasoning"]) > 0
        os.unlink(path)

    def test_result_structure(self, classifier):
        path = _write_temp("import os\n")
        result = classifier.classify(path, skip_cache=True)
        assert "file_path" in result
        assert "pattern" in result
        assert "ast" in result
        assert "final_category" in result
        assert "confidence" in result
        assert "reasoning" in result
        os.unlink(path)
