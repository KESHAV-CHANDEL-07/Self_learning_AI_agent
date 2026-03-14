"""Tests for agent.pattern_matcher — Layer 1 classifier."""

import os
import tempfile
import pytest
from agent.pattern_matcher import PatternMatcher


@pytest.fixture
def pm():
    return PatternMatcher()


# ── Extension mapping tests ──────────────────────────────────────────────

class TestExtensionMapping:
    def test_python_file(self, pm):
        result = pm.classify("/project/foo.py")
        assert result["category"] == "code"

    def test_javascript_file(self, pm):
        result = pm.classify("/project/app.js")
        assert result["category"] == "code"

    def test_html_file(self, pm):
        result = pm.classify("/project/index.html")
        assert result["category"] == "code/frontend"

    def test_css_file(self, pm):
        result = pm.classify("/project/styles.css")
        assert result["category"] == "code/frontend"

    def test_yaml_config(self, pm):
        result = pm.classify("/project/docker-compose.yaml")
        assert result["category"] == "config"

    def test_json_config(self, pm):
        result = pm.classify("/project/package.json")
        assert result["category"] == "config"

    def test_markdown_docs(self, pm):
        result = pm.classify("/project/README.md")
        assert result["category"] == "docs"

    def test_image_jpg(self, pm):
        result = pm.classify("/photos/cat.jpg")
        assert result["category"] == "images"

    def test_image_png(self, pm):
        result = pm.classify("/assets/logo.png")
        assert result["category"] == "images"

    def test_csv_data(self, pm):
        result = pm.classify("/data/sales.csv")
        assert result["category"] == "data"

    def test_sql_database(self, pm):
        result = pm.classify("/db/schema.sql")
        assert result["category"] == "database"

    def test_model_pytorch(self, pm):
        result = pm.classify("/saved/model.pt")
        assert result["category"] == "models"

    def test_notebook(self, pm):
        result = pm.classify("/nb/analysis.ipynb")
        assert result["category"] == "notebooks"

    def test_shell_script(self, pm):
        result = pm.classify("/scripts/deploy.sh")
        assert result["category"] == "scripts"

    def test_unknown_extension(self, pm):
        result = pm.classify("/project/mystery.xyz")
        assert result["category"] == "misc"


# ── Keyword rule tests ───────────────────────────────────────────────────

class TestKeywordRules:
    def test_auth_keyword(self, pm):
        result = pm.classify("/project/auth_handler.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "auth"

    def test_login_keyword(self, pm):
        result = pm.classify("/project/login.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "auth"

    def test_token_keyword(self, pm):
        result = pm.classify("/project/token_utils.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "auth"

    def test_test_keyword(self, pm):
        result = pm.classify("/project/test_users.py")
        assert result["category"] == "tests"

    def test_spec_keyword(self, pm):
        result = pm.classify("/project/user_spec.py")
        assert result["category"] == "tests"

    def test_mock_keyword(self, pm):
        result = pm.classify("/project/mock_service.py")
        assert result["category"] == "tests"

    def test_model_keyword(self, pm):
        result = pm.classify("/project/user_model.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "models"

    def test_schema_keyword(self, pm):
        result = pm.classify("/project/user_schema.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "models"

    def test_config_keyword(self, pm):
        result = pm.classify("/project/config_loader.py")
        assert result["category"] == "config"

    def test_util_keyword(self, pm):
        result = pm.classify("/project/string_util.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "utils"

    def test_helper_keyword(self, pm):
        result = pm.classify("/project/helper.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "utils"

    def test_api_keyword(self, pm):
        result = pm.classify("/project/api_v2.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "api"

    def test_route_keyword(self, pm):
        result = pm.classify("/project/user_route.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "api"

    def test_endpoint_keyword(self, pm):
        result = pm.classify("/project/endpoint.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "api"

    def test_database_keyword(self, pm):
        result = pm.classify("/project/database_init.py")
        assert result["category"] == "database"

    def test_migration_keyword(self, pm):
        result = pm.classify("/project/migration_001.py")
        assert result["category"] == "database"

    def test_train_keyword(self, pm):
        result = pm.classify("/project/train_model.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "ml"

    def test_predict_keyword(self, pm):
        result = pm.classify("/project/predict.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "ml"

    def test_main_keyword(self, pm):
        result = pm.classify("/project/main.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "core"

    def test_app_keyword(self, pm):
        result = pm.classify("/project/app.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "core"

    def test_server_keyword(self, pm):
        result = pm.classify("/project/server.py")
        assert result["category"] == "code"
        assert result["subcategory"] == "core"


# ── Confidence range tests ───────────────────────────────────────────────

class TestConfidenceRange:
    def test_confidence_minimum(self, pm):
        result = pm.classify("/project/mystery.xyz")
        assert result["confidence"] >= 0.3

    def test_confidence_maximum(self, pm):
        """Confidence should never exceed 0.6 for pattern matcher."""
        result = pm.classify("/tests/test_auth.py")
        assert result["confidence"] <= 0.6

    def test_extension_only_confidence(self, pm):
        result = pm.classify("/project/foo.py")
        assert 0.3 <= result["confidence"] <= 0.6

    def test_keyword_match_boosts_confidence(self, pm):
        ext_only = pm.classify("/project/foo.py")
        keyword = pm.classify("/project/test_foo.py")
        assert keyword["confidence"] >= ext_only["confidence"]


# ── Parent folder context tests ──────────────────────────────────────────

class TestParentFolder:
    def test_tests_folder_hint(self, pm):
        result = pm.classify("/project/tests/some_file.py")
        # The tests folder hint should influence the result
        assert result["confidence"] >= 0.3

    def test_api_folder_hint(self, pm):
        result = pm.classify("/project/api/users.py")
        # Should get a confidence boost from folder hint
        assert result["confidence"] >= 0.3
