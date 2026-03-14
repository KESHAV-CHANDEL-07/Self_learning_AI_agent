"""Tests for agent.ast_analyzer — Layer 2 classifier."""

import os
import tempfile
import textwrap
import pytest
from agent.ast_analyzer import ASTAnalyzer


@pytest.fixture
def analyzer():
    return ASTAnalyzer()


def _write_temp(content: str, suffix: str = ".py") -> str:
    """Write *content* to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(textwrap.dedent(content))
    return path


# ── Import detection tests ───────────────────────────────────────────────

class TestImportDetection:
    def test_flask_import(self, analyzer):
        path = _write_temp("import flask\n")
        result = analyzer.analyze(path)
        assert "flask" in result["imports"]
        assert result["detected_category"] == "code/api"
        os.unlink(path)

    def test_pytest_import(self, analyzer):
        path = _write_temp("import pytest\n")
        result = analyzer.analyze(path)
        assert "pytest" in result["imports"]
        assert result["detected_category"] == "tests"
        os.unlink(path)

    def test_sqlalchemy_import(self, analyzer):
        path = _write_temp("from sqlalchemy import Column\n")
        result = analyzer.analyze(path)
        assert "sqlalchemy" in result["imports"]
        assert result["detected_category"] == "database"
        os.unlink(path)

    def test_torch_import(self, analyzer):
        path = _write_temp("import torch\nimport torch.nn as nn\n")
        result = analyzer.analyze(path)
        assert "torch" in result["imports"]
        assert result["detected_category"] == "code/ml"
        os.unlink(path)

    def test_typer_import(self, analyzer):
        path = _write_temp("import typer\n")
        result = analyzer.analyze(path)
        assert "typer" in result["imports"]
        assert result["detected_category"] == "code/cli"
        os.unlink(path)


# ── Decorator detection tests ────────────────────────────────────────────

class TestDecoratorDetection:
    def test_route_decorator(self, analyzer):
        code = """\
        from flask import Flask
        app = Flask(__name__)

        @app.route("/")
        def index():
            return "hello"
        """
        path = _write_temp(code)
        result = analyzer.analyze(path)
        assert len(result["decorators"]) > 0
        assert result["detected_category"] == "code/api"
        os.unlink(path)

    def test_pytest_fixture_decorator(self, analyzer):
        code = """\
        import pytest

        @pytest.fixture
        def sample():
            return 42
        """
        path = _write_temp(code)
        result = analyzer.analyze(path)
        assert len(result["decorators"]) > 0
        assert result["detected_category"] == "tests"
        os.unlink(path)


# ── Class/function name pattern tests ────────────────────────────────────

class TestClassPatterns:
    def test_test_class(self, analyzer):
        code = """\
        class TestUserAuth:
            def test_login(self):
                pass
        """
        path = _write_temp(code)
        result = analyzer.analyze(path)
        assert "TestUserAuth" in result["classes"]
        assert result["detected_category"] == "tests"
        os.unlink(path)

    def test_model_class(self, analyzer):
        code = """\
        class UserModel:
            id = None
            name = None
        """
        path = _write_temp(code)
        result = analyzer.analyze(path)
        assert "UserModel" in result["classes"]
        assert result["detected_category"] == "code/models"
        os.unlink(path)

    def test_schema_class(self, analyzer):
        code = """\
        class UserSchema:
            pass
        """
        path = _write_temp(code)
        result = analyzer.analyze(path)
        assert "UserSchema" in result["classes"]
        assert result["detected_category"] == "code/models"
        os.unlink(path)

    def test_main_guard(self, analyzer):
        code = """\
        def main():
            pass

        if __name__ == "__main__":
            main()
        """
        path = _write_temp(code)
        result = analyzer.analyze(path)
        assert "__main__" in result["keywords"]
        assert result["detected_category"] == "code/core"
        os.unlink(path)

    def test_function_extraction(self, analyzer):
        code = """\
        def foo():
            pass

        def bar():
            pass
        """
        path = _write_temp(code)
        result = analyzer.analyze(path)
        assert "foo" in result["functions"]
        assert "bar" in result["functions"]
        os.unlink(path)


# ── Non-Python file handling tests ───────────────────────────────────────

class TestNonPythonFiles:
    def test_json_file(self, analyzer):
        path = _write_temp('{"name": "test", "version": "1.0"}', suffix=".json")
        result = analyzer.analyze(path)
        assert result["detected_category"] == "config"
        assert "name" in result["keywords"]
        os.unlink(path)

    def test_markdown_file(self, analyzer):
        path = _write_temp("# My Project\nThis is a readme file.\n", suffix=".md")
        result = analyzer.analyze(path)
        assert result["detected_category"] == "docs"
        assert "My Project" in result["keywords"]
        os.unlink(path)

    def test_html_file(self, analyzer):
        path = _write_temp("<html><head><title>My Page</title></head></html>", suffix=".html")
        result = analyzer.analyze(path)
        assert result["detected_category"] == "code/frontend"
        assert "My Page" in result["keywords"]
        os.unlink(path)

    def test_shell_file(self, analyzer):
        path = _write_temp("#!/bin/bash\n# Deploy script\necho hello\n", suffix=".sh")
        result = analyzer.analyze(path)
        assert result["detected_category"] == "scripts"
        os.unlink(path)

    def test_js_file(self, analyzer):
        path = _write_temp(
            'import express from "express";\nconst app = express();\n',
            suffix=".js"
        )
        result = analyzer.analyze(path)
        assert result["detected_category"] == "code/api"
        os.unlink(path)


# ── Confidence range tests ───────────────────────────────────────────────

class TestConfidenceRange:
    def test_confidence_minimum(self, analyzer):
        path = _write_temp("x = 1\n")
        result = analyzer.analyze(path)
        assert result["confidence"] >= 0.5
        os.unlink(path)

    def test_confidence_maximum(self, analyzer):
        path = _write_temp("import flask\nimport pytest\n")
        result = analyzer.analyze(path)
        assert result["confidence"] <= 0.9
        os.unlink(path)

    def test_empty_file(self, analyzer):
        path = _write_temp("")
        result = analyzer.analyze(path)
        assert result["confidence"] >= 0.5
        os.unlink(path)


# ── Syntax error handling ────────────────────────────────────────────────

class TestErrorHandling:
    def test_syntax_error(self, analyzer):
        path = _write_temp("def foo(:\n    pass\n")
        result = analyzer.analyze(path)
        # Should not crash, returns empty result
        assert result["detected_category"] is None
        assert result["confidence"] == 0.5
        os.unlink(path)

    def test_unsupported_extension(self, analyzer):
        path = _write_temp("some binary content", suffix=".bin")
        result = analyzer.analyze(path)
        assert result["detected_category"] is None
        os.unlink(path)
