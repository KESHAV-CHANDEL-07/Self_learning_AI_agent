"""
File Classifier — Combination Layer
====================================
Orchestrates the 3-layer classification pipeline:

1. **Pattern Matcher** (30 % weight) — extension / keyword / folder rules
2. **AST Analyzer**    (50 % weight) — code-structure analysis
3. **Local LLM**       (20 % weight) — Ollama fallback (only if needed)

Final results are cached in the ``classifications`` table via
:class:`agent.sqlite_dao.SQLiteDAO`.
"""

import hashlib
import os
from datetime import datetime, timezone
from typing import Dict, Optional

from agent.pattern_matcher import PatternMatcher
from agent.ast_analyzer import ASTAnalyzer
from agent.local_llm import LocalLLM
from agent.sqlite_dao import SQLiteDAO
from utils.logger import get_logger

logger = get_logger("FileClassifier")

WEIGHT_PATTERN = 0.30
WEIGHT_AST = 0.50
WEIGHT_LLM = 0.20

CONFIDENCE_THRESHOLD = 0.7  # triggers Layer 3


class FileClassifier:
    """Weighted combination of the 3 classification layers."""

    def __init__(self, use_llm: bool = False, dao: Optional[SQLiteDAO] = None):
        """
        Parameters
        ----------
        use_llm : bool
            When *True*, Layer 3 (Ollama) is eligible to run if combined
            confidence is below the threshold.  When *False*, Layer 3 is
            never invoked (equivalent to ``--use-ai`` being absent).
        dao : SQLiteDAO, optional
            DAO instance for caching.  Falls back to the default singleton.
        """
        self.pattern = PatternMatcher()
        self.ast = ASTAnalyzer()
        self.llm = LocalLLM()
        self.use_llm = use_llm
        self.dao = dao or SQLiteDAO()

    # ── public API ────────────────────────────────────────────────────────
    def classify(self, file_path: str, *, skip_cache: bool = False) -> Dict:
        """Classify a single file and return a result dict.

        Returns::

            {
                "file_path": "...",
                "pattern": {...},
                "ast": {...},
                "llm": {...} | None,
                "final_category": "...",
                "final_subcategory": "..." | None,
                "confidence": 0.0-1.0,
                "reasoning": "...",
            }
        """
        # ── cache look-up ────────────────────────────────────────────────
        if not skip_cache:
            file_hash = self._file_hash(file_path)
            cached = self.dao.get_classification_by_hash(file_hash)
            if cached:
                logger.debug(f"Cache hit for {file_path}")
                return cached

        # ── Layer 1 ──────────────────────────────────────────────────────
        pattern_result = self.pattern.classify(file_path)
        logger.debug(f"L1 PatternMatcher → {pattern_result}")

        # ── Layer 2 ──────────────────────────────────────────────────────
        ast_result = self.ast.analyze(file_path)
        logger.debug(f"L2 ASTAnalyzer → cat={ast_result.get('detected_category')}, "
                      f"conf={ast_result.get('confidence')}")

        # ── Combine L1 + L2 ──────────────────────────────────────────────
        combined_conf = (
            WEIGHT_PATTERN * pattern_result["confidence"]
            + WEIGHT_AST * ast_result["confidence"]
        )
        # Normalise over the 80% weight budget so far
        if combined_conf > 0:
            normalised_conf = combined_conf / (WEIGHT_PATTERN + WEIGHT_AST)
        else:
            normalised_conf = 0.0

        # ── Layer 3 (optional) ───────────────────────────────────────────
        llm_result: Optional[Dict] = None
        if self.use_llm and normalised_conf < CONFIDENCE_THRESHOLD:
            summary = {
                "filename": os.path.basename(file_path),
                "imports": ast_result.get("imports", []),
                "functions": ast_result.get("functions", []),
                "classes": ast_result.get("classes", []),
                "keywords": ast_result.get("keywords", []),
            }
            llm_result = self.llm.classify(summary)
            logger.debug(f"L3 LocalLLM → {llm_result}")

        # ── Final decision ───────────────────────────────────────────────
        final_cat, final_sub, final_conf, reasoning = self._decide(
            pattern_result, ast_result, llm_result
        )

        result = {
            "file_path": file_path,
            "pattern": pattern_result,
            "ast": {
                "detected_category": ast_result.get("detected_category"),
                "detected_subcategory": ast_result.get("detected_subcategory"),
                "confidence": ast_result.get("confidence"),
            },
            "llm": llm_result,
            "final_category": final_cat,
            "final_subcategory": final_sub,
            "confidence": final_conf,
            "reasoning": reasoning,
        }

        # ── persist to cache ─────────────────────────────────────────────
        self._save_to_cache(file_path, pattern_result, ast_result, llm_result,
                            final_cat, final_conf)
        return result

    # ── decision logic ────────────────────────────────────────────────────
    def _decide(self, pattern: Dict, ast_res: Dict,
                llm: Optional[Dict]):
        """Return ``(category, subcategory, confidence, reasoning)``."""

        p_cat = pattern.get("category")
        a_cat = ast_res.get("detected_category")
        l_cat = llm.get("category") if llm else None

        p_sub = pattern.get("subcategory")
        a_sub = ast_res.get("detected_subcategory")
        l_sub = llm.get("subcategory") if llm else None

        p_conf = pattern.get("confidence", 0)
        a_conf = ast_res.get("confidence", 0)
        l_conf = llm.get("confidence", 0) if llm else 0

        cats = [c for c in [p_cat, a_cat, l_cat] if c]

        # All 3 agree
        if l_cat and p_cat == a_cat == l_cat:
            reasoning = f"All 3 layers agree on '{p_cat}' → boosted to 0.95"
            return p_cat, (p_sub or a_sub or l_sub), 0.95, reasoning

        # 2 of 3 agree (majority)
        if l_cat:
            for candidate in [p_cat, a_cat, l_cat]:
                if candidate and cats.count(candidate) >= 2:
                    reasoning = (f"Majority decision: 2/3 layers agree on '{candidate}'")
                    conf = min(0.9, max(p_conf, a_conf, l_conf) + 0.05)
                    sub = self._pick_sub([p_sub, a_sub, l_sub],
                                         [p_cat, a_cat, l_cat], candidate)
                    return candidate, sub, round(conf, 2), reasoning

        # Only L1 + L2 available — weighted blend
        if a_cat:
            # If both agree without LLM
            if p_cat == a_cat:
                conf = (WEIGHT_PATTERN * p_conf + WEIGHT_AST * a_conf) / (WEIGHT_PATTERN + WEIGHT_AST)
                conf = min(0.9, conf + 0.1)
                reasoning = f"L1+L2 agree on '{a_cat}'"
                return a_cat, (a_sub or p_sub), round(conf, 2), reasoning

            # Disagree — AST wins (higher weight)
            reasoning = f"L1 says '{p_cat}', L2 says '{a_cat}' → using AST (50% weight)"
            return a_cat, a_sub, round(a_conf, 2), reasoning

        # All disagree or only pattern available
        if p_cat:
            reasoning = f"Only pattern match available: '{p_cat}'"
            return p_cat, p_sub, round(p_conf, 2), reasoning

        reasoning = "No layer could classify → misc"
        return "misc", None, 0.3, reasoning

    @staticmethod
    def _pick_sub(subs, cats, winner_cat):
        """Pick the subcategory from the layer(s) that voted for *winner_cat*."""
        for sub, cat in zip(subs, cats):
            if cat == winner_cat and sub:
                return sub
        return None

    # ── caching helpers ───────────────────────────────────────────────────
    @staticmethod
    def _file_hash(file_path: str) -> str:
        try:
            h = hashlib.sha256()
            with open(file_path, "rb") as fh:
                for chunk in iter(lambda: fh.read(8192), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return ""

    def _save_to_cache(self, file_path, pattern, ast_res, llm,
                       final_cat, final_conf):
        try:
            self.dao.save_classification(
                file_path=file_path,
                file_hash=self._file_hash(file_path),
                pattern_category=pattern.get("category"),
                ast_category=ast_res.get("detected_category"),
                llm_category=llm.get("category") if llm else None,
                final_category=final_cat,
                confidence=final_conf,
            )
        except Exception as exc:
            logger.debug(f"Could not cache classification: {exc}")
