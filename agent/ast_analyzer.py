"""
Layer 2 — AST Analyzer
======================
Reads code structure locally using Python's ``ast`` module (for ``.py``
files) and lightweight regex analysis for other file types.

No API, no cost.  Runs after Pattern Matcher.
Confidence range: 0.5 – 0.9
"""

import ast
import os
import re
import json
from typing import Dict, List, Optional

from utils.logger import get_logger

logger = get_logger("ASTAnalyzer")

# ── Import → category mapping ────────────────────────────────────────────
IMPORT_CATEGORY_MAP: Dict[str, str] = {
    # api / web
    "flask": "code/api", "fastapi": "code/api", "django": "code/api",
    "starlette": "code/api", "bottle": "code/api", "sanic": "code/api",
    "aiohttp": "code/api", "tornado": "code/api",
    # tests
    "pytest": "tests", "unittest": "tests", "nose": "tests",
    "mock": "tests", "hypothesis": "tests",
    # database
    "sqlalchemy": "database", "sqlite3": "database", "psycopg2": "database",
    "pymongo": "database", "peewee": "database", "alembic": "database",
    # ml
    "torch": "code/ml", "tensorflow": "code/ml", "keras": "code/ml",
    "sklearn": "code/ml", "transformers": "code/ml", "numpy": "code/ml",
    "pandas": "code/ml", "scipy": "code/ml", "xgboost": "code/ml",
    # cli
    "typer": "code/cli", "click": "code/cli", "argparse": "code/cli",
    # auth
    "jwt": "code/auth", "passlib": "code/auth", "bcrypt": "code/auth",
    "oauthlib": "code/auth",
}

# ── Decorator → category mapping ─────────────────────────────────────────
DECORATOR_PATTERNS = [
    (re.compile(r"app\.route|router\.(get|post|put|delete|patch)"), "code/api"),
    (re.compile(r"pytest\.fixture|pytest\.mark"), "tests"),
    (re.compile(r"property"), "code/models"),
    (re.compile(r"login_required|requires_auth"), "code/auth"),
]

# ── Class-name patterns ──────────────────────────────────────────────────
CLASS_PATTERNS = [
    (re.compile(r"Test", re.IGNORECASE), "tests"),
    (re.compile(r"Model|Schema|Entity", re.IGNORECASE), "code/models"),
    (re.compile(r"View|Viewset|Controller", re.IGNORECASE), "code/api"),
    (re.compile(r"Middleware|Auth|Permission", re.IGNORECASE), "code/auth"),
]


class ASTAnalyzer:
    """Layer 2 classifier — code-structure analysis."""

    # ── public API ────────────────────────────────────────────────────────
    def analyze(self, file_path: str) -> Dict:
        """Analyse *file_path* and return a detailed classification dict.

        Returns::

            {
                "imports": [...],
                "functions": [...],
                "classes": [...],
                "decorators": [...],
                "keywords": [...],
                "detected_category": "...",
                "detected_subcategory": "...",
                "confidence": 0.0-1.0,
            }
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".py":
            return self._analyze_python(file_path)
        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            return self._analyze_js(file_path)
        elif ext in (".json",):
            return self._analyze_json(file_path)
        elif ext in (".yaml", ".yml"):
            return self._analyze_yaml(file_path)
        elif ext == ".md":
            return self._analyze_markdown(file_path)
        elif ext == ".html":
            return self._analyze_html(file_path)
        elif ext in (".sh", ".bat", ".ps1"):
            return self._analyze_shell(file_path)
        else:
            return self._empty_result()

    # ── Python analysis ───────────────────────────────────────────────────
    def _analyze_python(self, file_path: str) -> Dict:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                source = fh.read()
            tree = ast.parse(source, filename=file_path)
        except SyntaxError:
            logger.debug(f"SyntaxError parsing {file_path}, falling back")
            return self._empty_result()
        except Exception as exc:
            logger.debug(f"Cannot parse {file_path}: {exc}")
            return self._empty_result()

        imports = self._extract_imports(tree)
        functions = self._extract_functions(tree)
        classes = self._extract_classes(tree)
        decorators = self._extract_decorators(tree)
        keywords: List[str] = []

        # Check for if __name__ == "__main__"
        has_main_guard = self._has_main_guard(tree)
        if has_main_guard:
            keywords.append("__main__")

        # ── Determine category from signals ──────────────────────────────
        category_votes: Dict[str, float] = {}

        # imports
        for imp in imports:
            top = imp.split(".")[0]
            cat = IMPORT_CATEGORY_MAP.get(top)
            if cat:
                category_votes[cat] = category_votes.get(cat, 0) + 0.25

        # decorators
        for dec in decorators:
            for pat, cat in DECORATOR_PATTERNS:
                if pat.search(dec):
                    category_votes[cat] = category_votes.get(cat, 0) + 0.3

        # class names
        for cls in classes:
            for pat, cat in CLASS_PATTERNS:
                if pat.search(cls):
                    category_votes[cat] = category_votes.get(cat, 0) + 0.2

        # main guard
        if has_main_guard:
            category_votes["code/core"] = category_votes.get("code/core", 0) + 0.3

        # Pick winner
        detected_category, confidence = self._pick_winner(category_votes)

        # Determine subcategory from category
        detected_subcategory = None
        if detected_category and "/" in detected_category:
            parts = detected_category.split("/", 1)
            detected_subcategory = parts[1]

        return {
            "imports": imports,
            "functions": functions,
            "classes": classes,
            "decorators": decorators,
            "keywords": keywords,
            "detected_category": detected_category,
            "detected_subcategory": detected_subcategory,
            "confidence": confidence,
        }

    # ── JS/TS analysis ────────────────────────────────────────────────────
    def _analyze_js(self, file_path: str) -> Dict:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                source = fh.read()
        except Exception:
            return self._empty_result()

        # Extract import/require statements
        import_re = re.compile(
            r"""(?:import\s+.*?\s+from\s+['"](.*?)['"]|require\s*\(\s*['"](.*?)['"]\s*\))"""
        )
        imports = [m.group(1) or m.group(2) for m in import_re.finditer(source)]

        # Extract function names
        fn_re = re.compile(r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\()")
        functions = [m.group(1) or m.group(2) for m in fn_re.finditer(source)]

        # Extract class names
        cls_re = re.compile(r"class\s+(\w+)")
        classes = [m.group(1) for m in cls_re.finditer(source)]

        keywords: List[str] = []
        category_votes: Dict[str, float] = {}

        # Check common JS framework imports
        js_import_map = {
            "express": "code/api", "koa": "code/api", "hapi": "code/api",
            "react": "code/frontend", "vue": "code/frontend", "angular": "code/frontend",
            "jest": "tests", "mocha": "tests", "chai": "tests",
            "mongoose": "database", "sequelize": "database",
            "tensorflow": "code/ml",
        }
        for imp in imports:
            pkg = imp.split("/")[0].lstrip("@")
            cat = js_import_map.get(pkg)
            if cat:
                category_votes[cat] = category_votes.get(cat, 0) + 0.25

        detected_category, confidence = self._pick_winner(category_votes)
        detected_subcategory = None
        if detected_category and "/" in detected_category:
            detected_subcategory = detected_category.split("/", 1)[1]

        return {
            "imports": imports,
            "functions": functions,
            "classes": classes,
            "decorators": [],
            "keywords": keywords,
            "detected_category": detected_category,
            "detected_subcategory": detected_subcategory,
            "confidence": confidence,
        }

    # ── JSON analysis ─────────────────────────────────────────────────────
    def _analyze_json(self, file_path: str) -> Dict:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                data = json.load(fh)
        except Exception:
            return self._empty_result()

        keywords: List[str] = []
        if isinstance(data, dict):
            keywords = list(data.keys())[:20]

        # Check for known config keys
        config_keys = {"name", "version", "dependencies", "devDependencies", "scripts"}
        if isinstance(data, dict) and config_keys & set(data.keys()):
            return {**self._empty_result(), "keywords": keywords,
                    "detected_category": "config", "confidence": 0.8}

        return {**self._empty_result(), "keywords": keywords,
                "detected_category": "config", "confidence": 0.6}

    # ── YAML analysis ─────────────────────────────────────────────────────
    def _analyze_yaml(self, file_path: str) -> Dict:
        try:
            import yaml  # type: ignore
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                data = yaml.safe_load(fh)
        except Exception:
            return {**self._empty_result(), "detected_category": "config", "confidence": 0.5}

        keywords: List[str] = []
        if isinstance(data, dict):
            keywords = list(data.keys())[:20]

        return {**self._empty_result(), "keywords": keywords,
                "detected_category": "config", "confidence": 0.7}

    # ── Markdown analysis ─────────────────────────────────────────────────
    def _analyze_markdown(self, file_path: str) -> Dict:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                lines = [l.strip() for l in fh.readlines()[:10]]
        except Exception:
            return self._empty_result()

        heading = ""
        first_line = ""
        for line in lines:
            if line.startswith("# ") and not heading:
                heading = line[2:].strip()
            elif line and not first_line and not line.startswith("#"):
                first_line = line
                break

        keywords = [heading, first_line] if heading else [first_line] if first_line else []
        return {**self._empty_result(), "keywords": keywords,
                "detected_category": "docs", "confidence": 0.7}

    # ── HTML analysis ─────────────────────────────────────────────────────
    def _analyze_html(self, file_path: str) -> Dict:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                source = fh.read(4096)
        except Exception:
            return self._empty_result()

        title_m = re.search(r"<title>(.*?)</title>", source, re.IGNORECASE | re.DOTALL)
        meta_m = re.findall(r'<meta\s+[^>]*content="(.*?)"', source, re.IGNORECASE)

        keywords: List[str] = []
        if title_m:
            keywords.append(title_m.group(1).strip())
        keywords.extend(meta_m[:3])

        return {**self._empty_result(), "keywords": keywords,
                "detected_category": "code/frontend", "confidence": 0.7}

    # ── Shell script analysis ─────────────────────────────────────────────
    def _analyze_shell(self, file_path: str) -> Dict:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()[:30]
        except Exception:
            return self._empty_result()

        comments = [l.strip() for l in lines if l.strip().startswith("#")]
        commands = [l.strip() for l in lines
                    if l.strip() and not l.strip().startswith("#")]

        return {
            **self._empty_result(),
            "keywords": (comments[:5] + commands[:5]),
            "detected_category": "scripts",
            "confidence": 0.7,
        }

    # ── AST helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _extract_imports(tree: ast.Module) -> List[str]:
        imports: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    @staticmethod
    def _extract_functions(tree: ast.Module) -> List[str]:
        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

    @staticmethod
    def _extract_classes(tree: ast.Module) -> List[str]:
        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        ]

    @staticmethod
    def _extract_decorators(tree: ast.Module) -> List[str]:
        decorators: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for dec in node.decorator_list:
                    decorators.append(ast.dump(dec))
        return decorators

    @staticmethod
    def _has_main_guard(tree: ast.Module) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                try:
                    test = node.test
                    if isinstance(test, ast.Compare):
                        left = test.left
                        if isinstance(left, ast.Name) and left.id == "__name__":
                            return True
                        if isinstance(left, ast.Constant) and left.value == "__main__":
                            return True
                except Exception:
                    pass
        return False

    # ── Scoring helpers ───────────────────────────────────────────────────
    @staticmethod
    def _pick_winner(votes: Dict[str, float]):
        if not votes:
            return None, 0.5
        winner = max(votes, key=votes.get)  # type: ignore[arg-type]
        raw = votes[winner]
        # Clamp confidence into 0.5 – 0.9
        confidence = min(0.9, max(0.5, 0.5 + raw))
        return winner, round(confidence, 2)

    @staticmethod
    def _empty_result() -> Dict:
        return {
            "imports": [],
            "functions": [],
            "classes": [],
            "decorators": [],
            "keywords": [],
            "detected_category": None,
            "detected_subcategory": None,
            "confidence": 0.5,
        }
