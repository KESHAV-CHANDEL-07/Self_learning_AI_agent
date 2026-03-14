"""
Layer 3 — Local LLM (Ollama)
============================
Optional classification layer that queries a locally-running Ollama
instance.  Only called when Layer 1 + Layer 2 combined confidence is
below 0.7.

* Model: ``llama3.2``
* Never sends full file content — only a structured summary.
* Graceful fallback when Ollama is not installed.
* Timeout: 10 seconds per file.
* Confidence range: 0.6 – 0.95
"""

import json
import re
from typing import Dict, Optional

from utils.logger import get_logger

logger = get_logger("LocalLLM")

OLLAMA_MODEL = "llama3.2"

VALID_CATEGORIES = {
    "api", "auth", "database", "models", "utils", "tests",
    "config", "ml", "cli", "core", "docs", "code", "scripts",
    "images", "data", "notebooks", "misc",
    # compound
    "code/api", "code/auth", "code/models", "code/utils",
    "code/ml", "code/cli", "code/core", "code/frontend",
}

_OLLAMA_AVAILABLE: Optional[bool] = None  # cached probe result


def _check_ollama() -> bool:
    """Return True if the ``ollama`` package is importable."""
    global _OLLAMA_AVAILABLE
    if _OLLAMA_AVAILABLE is not None:
        return _OLLAMA_AVAILABLE
    try:
        import ollama as _  # noqa: F401
        _OLLAMA_AVAILABLE = True
    except ImportError:
        _OLLAMA_AVAILABLE = False
    return _OLLAMA_AVAILABLE


class LocalLLM:
    """Layer 3 classifier — Ollama LLM fallback."""

    def __init__(self, model: str = OLLAMA_MODEL, timeout: int = 10):
        self.model = model
        self.timeout = timeout

    # ── public API ────────────────────────────────────────────────────────
    def classify(self, summary: Dict) -> Dict:
        """Classify based on a pre-built *summary* dict.

        *summary* should contain keys like ``filename``, ``imports``,
        ``functions``, ``classes``, ``keywords``.

        Returns ``{category, subcategory, confidence, reason}`` or a
        fallback dict when Ollama is unavailable.
        """
        if not _check_ollama():
            logger.warning(
                "Ollama not found. Run: ollama pull llama3.2"
            )
            return self._fallback()

        prompt = self._build_prompt(summary)

        try:
            import ollama  # type: ignore

            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={"timeout": self.timeout},
            )
            raw = response["message"]["content"]
            return self._parse_response(raw)
        except Exception as exc:
            logger.warning(f"Ollama classification failed: {exc}")
            return self._fallback()

    # ── internals ─────────────────────────────────────────────────────────
    @staticmethod
    def _build_prompt(summary: Dict) -> str:
        filename = summary.get("filename", "unknown")
        imports = ", ".join(summary.get("imports", [])[:15]) or "none"
        functions = ", ".join(summary.get("functions", [])[:15]) or "none"
        classes = ", ".join(summary.get("classes", [])[:15]) or "none"
        keywords = ", ".join(str(k) for k in summary.get("keywords", [])[:15]) or "none"

        return (
            f"File: {filename}\n"
            f"Imports: {imports}\n"
            f"Functions: {functions}\n"
            f"Classes: {classes}\n"
            f"Keywords: {keywords}\n"
            "\n"
            "Which category does this belong to?\n"
            "Choose from: api, auth, database, models, utils, tests, "
            "config, ml, cli, core, docs\n"
            "\n"
            "Reply with JSON only:\n"
            '{"category": "...", "subcategory": "...", '
            '"confidence": 0.0, "reason": "..."}'
        )

    def _parse_response(self, raw: str) -> Dict:
        """Try to extract a JSON dict from the LLM's response."""
        # Try to find JSON in the response
        json_match = re.search(r"\{[^{}]+\}", raw, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                cat = parsed.get("category", "misc")
                sub = parsed.get("subcategory")
                conf = float(parsed.get("confidence", 0.7))
                reason = parsed.get("reason", "")

                # Validate
                if cat not in VALID_CATEGORIES:
                    cat = "misc"
                # Clamp confidence 0.6 – 0.95
                conf = min(0.95, max(0.6, conf))

                return {
                    "category": cat,
                    "subcategory": sub,
                    "confidence": round(conf, 2),
                    "reason": reason,
                }
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        logger.debug(f"Could not parse LLM response: {raw[:200]}")
        return self._fallback()

    @staticmethod
    def _fallback() -> Dict:
        return {
            "category": None,
            "subcategory": None,
            "confidence": 0.0,
            "reason": "Ollama unavailable or response unparseable",
        }
