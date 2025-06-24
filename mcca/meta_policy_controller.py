# File: mcca/meta_policy_controller.py
"""
MetaPolicyController v3.2
-------------------------
Context-sensitive blend generator.

Primary API
-----------
get_strategy_weights(
    regime: str,
    board: chess.Board,
    features: dict,
    history: list,
    opponent_type: str,
    module_trace: dict | None = None,
) -> tuple[dict[str, float], dict[str, any]]

Returns
-------
weights      : Normalised dict {module_name: weight}
diagnostics  : {
                 "boost": [modules],
                 "suppress": [modules],
                 "reflex": bool,
                 "collapse_penalty": bool,
                 "mismatch_adjust": bool,
                 "raw": raw_dict_before_norm
               }
"""

from __future__ import annotations
from typing import Dict, Any, Tuple, List
import math
from mcca.regime_detector import RegimeDetector


class MetaPolicyController:
    # --------------------------------------------------------------- #
    # STATIC BASE WEIGHTS (soft priors)
    # --------------------------------------------------------------- #
    _BASE = {
        "tactical":   {"tactical": 1.0, "positional": 0.1, "shaping": 0.1, "deception": 0.1},
        "positional": {"positional": 0.6, "tactical": 0.2, "shaping": 0.1, "deception": 0.1},
        "shaping":    {"shaping": 0.5, "tactical": 0.3, "deception": 0.1, "positional": 0.1},
        "deception":  {"deception": 0.6, "shaping": 0.2, "tactical": 0.1, "positional": 0.1}
    }

    # --------------------------------------------------------------- #
    def __init__(self):
        # simple regret counters per module
        self.regret: Dict[str, float] = {m: 0.0 for m in ["tactical", "positional", "shaping", "deception"]}
        self.decay = 0.9  # exponential decay for regret

    # --------------------------------------------------------------- #
    def get_strategy_weights(
        self,
        regime: str,
        board,
        features: Dict[str, Any],
        history: list,
        opponent_type: str,
        module_trace: Dict[str, Any] | None = None
    ) -> Tuple[Dict[str, float], Dict[str, Any]]:
        # check for immediate tactical danger override
        checks, attackers = RegimeDetector._tactical_danger_zone(board)
        if (board.is_check() or checks >= 2 or attackers >= 3) and regime == "tactical":
            w = {
                "tactical": 0.85,
                "shaping": 0.05,
                "positional": 0.05,
                "deception": 0.05,
            }
            diag = {
                "boost": [],
                "suppress": [],
                "reflex": True,
                "collapse_penalty": False,
                "mismatch_adjust": False,
                "raw": w.copy(),
            }
            return w, diag

        # 1. ---- Start from base ------------------------------------ #
        weights = dict(self._BASE.get(regime, self._BASE["tactical"]))
        diag: Dict[str, Any] = {"boost": [], "suppress": [], "reflex": False,
                                "collapse_penalty": False, "mismatch_adjust": False,
                                "raw": weights.copy()}

        # 2. ---- Collapse / King-threat reflex ---------------------- #
        if features["in_check"] or features["king_exposure_score"] >= 3:
            _boost(weights, "tactical", +0.3, diag, label="check_reflex")

        if features["eval_delta"] is not None and features["eval_delta"] <= -150:
            _boost(weights, "tactical", +0.2, diag, label="eval_drop")
            diag["collapse_penalty"] = True

        # 3. ---- Module suppression flag --------------------------- #
        if module_trace:
            for mod, d in module_trace.items():
                if d.get("suppress", False):
                    _boost(weights, mod, -0.6, diag, label=f"{mod}_suppress")

        # 4. ---- Regret memory ------------------------------------- #
        for mod, wt in list(weights.items()):
            if self.regret.get(mod, 0) > 0.5:  # high regret → dampen
                _boost(weights, mod, -0.3, diag, label=f"{mod}_regret")

        # 5. ---- Opponent mismatch --------------------------------- #
        if opponent_type == "positional" and regime == "deception":
            _boost(weights, "shaping", +0.25, diag, label="opp_mismatch")
            diag["mismatch_adjust"] = True
        elif opponent_type == "tactical" and regime == "positional":
            _boost(weights, "shaping", +0.2, diag, label="opp_mismatch")
            diag["mismatch_adjust"] = True

        # 6. ---- Normalise weights --------------------------------- #
        weights = _softmax_normalise(weights)

        # 7. ---- Update regret memory ------------------------------ #
        self._update_regret(module_trace, features)

        return weights, diag

    # --------------------------------------------------------------- #
    # INTERNAL UTILS
    # --------------------------------------------------------------- #
    def _update_regret(self, module_trace: Dict[str, Any] | None, features):
        """Increment regret for modules that contributed to eval drop."""
        # decay previous regret
        self.regret = {m: v * self.decay for m, v in self.regret.items()}
        if module_trace and features.get("eval_delta") and features["eval_delta"] < -50:
            # blame primary module (= largest weight in trace) if eval dropped
            worst = max(module_trace.items(), key=lambda kv: kv[1].get("risk", 0))[0]
            self.regret[worst] = min(self.regret.get(worst, 0) + 0.3, 1.0)


# -------------------------------------------------------------------- #
# HELPER FUNCTIONS (module-local)
# -------------------------------------------------------------------- #
def _boost(w: Dict[str, float], mod: str, delta: float, diag: dict, label: str):
    prev = w.get(mod, 0.0)
    w[mod] = max(prev + delta, 0.0)
    if delta > 0:
        diag["boost"].append(label)
    else:
        diag["suppress"].append(label)


def _softmax_normalise(w: Dict[str, float]) -> Dict[str, float]:
    """Convert arbitrary positives/negatives into softmax (all ≥0)."""
    # shift to ensure non-negative
    min_val = min(w.values())
    if min_val < 0:
        w = {k: v - min_val for k, v in w.items()}

    exp_vals = {k: math.exp(v) for k, v in w.items()}
    total = sum(exp_vals.values()) or 1.0
    return {k: round(v / total, 3) for k, v in exp_vals.items()}
