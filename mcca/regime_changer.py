# File: mcca/regime_changer.py
"""
RegimeChanger v3.2
------------------
Receives a *raw* regime suggestion from RegimeDetector plus a symbolic
context bundle, and decides the **final regime** for the current move.

Key Responsibilities
--------------------
1.  Collapse Reflex
    - Immediate override to "tactical" on check, king exposure ≥ 3, or
      ≥ 150 cp evaluation drop.

2.  Fatigue & Loop Avoidance
    - Detect long unbroken sequences of a single regime and force a fresh
      regime (default "tactical").

3.  Opponent-Profile Adaptation
    - Adjust regime when it plays directly into the opponent’s strength.

4.  Module-Suppression Fallback
    - If the module *aligned* with the chosen regime has `suppress=True`,
      shift to an unsuppressed neighbour regime.

Returns
-------
final_regime : str
overridden   : bool
reason       : str   (human-readable explanation)
"""

from __future__ import annotations
from typing import Dict, Any, List


class RegimeChanger:
    """Context-aware regime override engine."""

    def __init__(self):
        self.prev_regimes: List[str] = []
        self.fatigue_window = 4          # N identical regimes → fatigue

    # ------------------------------------------------------------------ #
    def decide(
        self,
        raw_regime: str,
        features: Dict[str, Any],
        opponent_type: str,
        module_trace: Dict[str, Any] | None = None
    ) -> tuple[str, bool, str]:
        """
        Parameters
        ----------
        raw_regime : str
            Proposed regime from RegimeDetector.
        features : dict
            Symbolic vector produced by RegimeDetector.extract_features().
        opponent_type : str
            Classification from OpponentClassifier ('tactical', 'positional', etc.).
        module_trace : dict | None
            Diagnostics from each module for this move
            e.g.  {"tactical": {...}, "positional": {...}, ...}

        Returns
        -------
        final_regime, overridden_flag, reason
        """
        overridden = False
        reason_parts: List[str] = []

        # ----------------- 1. Collapse Reflex -------------------------- #
        if features["in_check"] \
           or features["king_exposure_score"] >= 3 \
           or (features["eval_delta"] is not None
               and features["eval_delta"] <= -150):
            raw_regime = "tactical"
            overridden = True
            reason_parts.append("collapse_reflex")

        # ----------------- 2. Fatigue Avoidance ------------------------ #
        if self._fatigue_detected(raw_regime):
            raw_regime = "tactical"
            overridden = True
            reason_parts.append("fatigue_reset")

        # ----------------- 3. Opponent Mismatch ------------------------ #
        mismatch_regime = self._mismatch_adjust(raw_regime, opponent_type)
        if mismatch_regime != raw_regime:
            overridden = True
            reason_parts.append(f"opponent_mismatch:{opponent_type}")
        final_regime = mismatch_regime

        # ----------------- 4. Module Suppression ----------------------- #
        if module_trace:
            primary_module = final_regime          # name matches module
            diag = module_trace.get(primary_module, {})
            if diag and diag.get("suppress", False):
                # pick tactical as safe fallback
                final_regime = "tactical"
                overridden = True
                reason_parts.append(f"{primary_module}_suppressed")

        # ----------------- 5. Memory Update ---------------------------- #
        self.prev_regimes.append(final_regime)
        if len(self.prev_regimes) > 8:
            self.prev_regimes.pop(0)

        reason = ", ".join(reason_parts) if reason_parts else "accepted"
        return final_regime, overridden, reason

    # ------------------------------------------------------------------ #
    # INTERNAL HELPERS
    # ------------------------------------------------------------------ #
    def _fatigue_detected(self, regime: str) -> bool:
        if len(self.prev_regimes) < self.fatigue_window:
            return False
        return all(r == regime for r in self.prev_regimes[-self.fatigue_window:])

    @staticmethod
    def _mismatch_adjust(regime: str, opponent: str) -> str:
        """
        Simple mismatch table:
          - Positional opponent vs Deception → switch to Shaping
          - Tactical opponent vs Positional → switch to Shaping
          - Adaptive opponent → no change
        """
        if opponent == "positional" and regime == "deception":
            return "shaping"
        if opponent == "tactical" and regime == "positional":
            return "shaping"
        return regime
