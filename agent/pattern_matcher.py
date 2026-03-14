"""
Layer 1 — Pattern Matcher
=========================
Fast, rule-based file classifier.  Always runs first.

Uses file extension, filename keywords, and parent folder name to
produce a baseline ``{category, subcategory, confidence}`` dict.
Confidence range: 0.3 – 0.6
"""

import os
from typing import Dict, Optional

# ── Extension → base category ────────────────────────────────────────────
EXTENSION_MAP: Dict[str, str] = {
    # code
    ".py": "code", ".js": "code", ".ts": "code", ".java": "code",
    ".cpp": "code", ".c": "code", ".go": "code", ".rs": "code",
    # code/frontend
    ".html": "code/frontend", ".css": "code/frontend", ".jsx": "code/frontend",
    ".tsx": "code/frontend", ".vue": "code/frontend", ".scss": "code/frontend",
    # config
    ".yaml": "config", ".yml": "config", ".json": "config", ".toml": "config",
    ".env": "config", ".cfg": "config", ".ini": "config",
    # docs
    ".md": "docs", ".rst": "docs", ".txt": "docs", ".pdf": "docs",
    # images
    ".jpg": "images", ".jpeg": "images", ".png": "images", ".gif": "images",
    ".svg": "images", ".ico": "images", ".webp": "images",
    # data
    ".csv": "data", ".xlsx": "data", ".parquet": "data", ".jsonl": "data",
    # database
    ".db": "database", ".sqlite": "database", ".sql": "database",
    # ML models
    ".pt": "models", ".pth": "models", ".pkl": "models",
    ".h5": "models", ".onnx": "models",
    # notebooks
    ".ipynb": "notebooks",
    # scripts
    ".sh": "scripts", ".bat": "scripts", ".ps1": "scripts",
    # audio
    ".mp3": "misc", ".wav": "misc", ".flac": "misc", ".ogg": "misc",
    # video
    ".mp4": "misc", ".mkv": "misc", ".avi": "misc", ".mov": "misc",
    # archives
    ".zip": "misc", ".tar.gz": "misc", ".rar": "misc", ".7z": "misc",
}

# ── Filename keywords → subcategory ──────────────────────────────────────
KEYWORD_RULES = [
    (["auth", "login", "token"],                          "code", "auth"),
    (["test", "spec", "mock"],                            "tests", None),
    (["model", "schema", "entity"],                       "code", "models"),
    (["config", "settings", "env"],                       "config", None),
    (["util", "helper", "common"],                        "code", "utils"),
    (["api", "route", "endpoint", "view"],                "code", "api"),
    (["db", "database", "migration"],                     "database", None),
    (["train", "predict", "infer", "nn"],                 "code", "ml"),
    (["main", "app", "server", "run"],                    "code", "core"),
]

# ── Parent folder name → context hints ───────────────────────────────────
FOLDER_HINTS: Dict[str, str] = {
    "tests": "tests",
    "test": "tests",
    "spec": "tests",
    "api": "code/api",
    "routes": "code/api",
    "models": "code/models",
    "schemas": "code/models",
    "utils": "code/utils",
    "helpers": "code/utils",
    "config": "config",
    "configs": "config",
    "migrations": "database",
    "ml": "code/ml",
    "auth": "code/auth",
    "docs": "docs",
    "scripts": "scripts",
    "data": "data",
    "static": "code/frontend",
    "templates": "code/frontend",
    "core": "code/core",
    "cli": "code/cli",
}


class PatternMatcher:
    """Layer 1 classifier — extension + keyword + folder heuristics."""

    # ── public API ────────────────────────────────────────────────────────
    def classify(self, file_path: str) -> Dict:
        """Return ``{category, subcategory, confidence}`` for *file_path*.

        Confidence is always in the 0.3 – 0.6 range.
        """
        filename = os.path.basename(file_path).lower()
        _, ext = os.path.splitext(filename)
        parent = os.path.basename(os.path.dirname(file_path)).lower()

        category: Optional[str] = None
        subcategory: Optional[str] = None
        confidence: float = 0.3

        # 1. Extension-based category ----------------------------------
        ext_category = EXTENSION_MAP.get(ext)
        if ext_category:
            category = ext_category
            confidence = 0.4

        # 2. Keyword-based subcategory ---------------------------------
        kw_cat, kw_sub = self._match_keywords(filename)
        if kw_cat:
            category = kw_cat
            subcategory = kw_sub
            confidence = 0.5

        # 3. Parent folder context hint --------------------------------
        folder_hint = FOLDER_HINTS.get(parent)
        if folder_hint:
            # If folder hint agrees with what we already have, boost
            if category and folder_hint.startswith(category.split("/")[0]):
                confidence = min(confidence + 0.1, 0.6)
            elif not category:
                category = folder_hint
                confidence = 0.45

        # Fallback
        if not category:
            category = "misc"
            confidence = 0.3

        return {
            "category": category,
            "subcategory": subcategory,
            "confidence": round(confidence, 2),
        }

    # ── internals ─────────────────────────────────────────────────────────
    @staticmethod
    def _match_keywords(filename: str):
        """Return ``(category, subcategory)`` from keyword rules, or ``(None, None)``."""
        name_no_ext = os.path.splitext(filename)[0]
        for keywords, cat, sub in KEYWORD_RULES:
            for kw in keywords:
                if kw in name_no_ext:
                    return cat, sub
        return None, None
