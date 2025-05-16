# File: mcca/agent.py
from __future__ import annotations
import random
import chess
from typing import Dict, Any, Tuple, List

from mcca.meta_policy_controller import MetaPolicyController
from mcca.regime_detector import RegimeDetector
from mcca.regime_changer import RegimeChanger
from mcca.opponent_classifier import OpponentClassifier

# v3.2 modules (all return `(move, diag)`):
from mcca.modules.tactical_module import TacticalModule
from mcca.modules.shaping_module import ShapingModule
from mcca.modules.positional_module import PositionalModule
from mcca.modules.deception_module import DeceptionModule


class MCCAAgent:
    """
    Top-level agent orchestrator for MCCA v3.2
    ------------------------------------------
    Pipeline:
        1. OpponentClassifier   – update on their last move
        2. RegimeDetector       – extract features & propose raw regime
        3. RegimeChanger        – override / stabilise regime
        4. MetaPolicyController – compute module blending weights
        5. Modules              – each proposes move + diag
        6. Weighted Blend       – choose final move
        7. Trace logging        – store symbolic history
    """

    # --------------------------------------------------------------- #
    def __init__(
        self,
        regime_detector: RegimeDetector | None = None,
        regime_changer: RegimeChanger | None = None,
        meta_controller: MetaPolicyController | None = None,
        modules: Dict[str, Any] | None = None
    ):
        self.regime_detector = regime_detector or RegimeDetector()
        self.regime_changer = regime_changer or RegimeChanger()
        self.meta_controller = meta_controller or MetaPolicyController()
        self.modules = modules or {
            "tactical": TacticalModule(),
            "shaping": ShapingModule(),
            "positional": PositionalModule(),
            "deception": DeceptionModule()
        }

        self.opponent_classifier = OpponentClassifier()
        self.history: List[Tuple[chess.Board, chess.Move, str]] = []

    # --------------------------------------------------------------- #
    def act(self, board: chess.Board) -> Tuple[chess.Move, Dict[str, Any]]:
        # ----------------------------------------------------------- #
        # 1. Update opponent classifier if opponent just moved
        # ----------------------------------------------------------- #
        if self.history:
            last_board, last_move, _ = self.history[-1]
            if last_board.turn != board.turn:          # colour switched
                self.opponent_classifier.update(last_board, last_move)

        opponent_profile = self.opponent_classifier.classify()
        opponent_type = opponent_profile["type"]

        # ----------------------------------------------------------- #
        # 2. Run RegimeDetector   (we pass None for eval_obj here; could
        #    be enhanced later with tactical quick-eval to supply cp)
        # ----------------------------------------------------------- #
        raw_regime, features = self.regime_detector.predict(
            board,
            self.history,
            eval_obj=None
        )

        # ----------------------------------------------------------- #
        # 3. Module draft moves + diagnostics  (needed for changer)
        # ----------------------------------------------------------- #
        legal_moves = list(board.legal_moves)
        module_trace: Dict[str, Any] = {}
        module_moves: Dict[str, chess.Move] = {}

        for name, module in self.modules.items():
            mv, diag = module.act(board)
            if mv not in legal_moves:                      # safety fallback
                mv = random.choice(legal_moves)
                diag["suppress"] = True
                diag["reason"] = diag.get("reason", "") + " | illegal-fallback"
            module_moves[name] = mv
            module_trace[name] = diag

        # ----------------------------------------------------------- #
        # 4. RegimeChanger override / stabilise
        # ----------------------------------------------------------- #
        final_regime, overridden, rc_reason = self.regime_changer.decide(
            raw_regime, features, opponent_type, module_trace
        )

        # ----------------------------------------------------------- #
        # 5. MetaPolicyController → weights
        # ----------------------------------------------------------- #
        weights, mpc_diag = self.meta_controller.get_strategy_weights(
            final_regime, board, features, self.history, opponent_type, module_trace
        )

        # ----------------------------------------------------------- #
        # 6. Weighted Blend  (vote by weights)
        # ----------------------------------------------------------- #
        move_scores: Dict[chess.Move, float] = {}
        for name, mv in module_moves.items():
            move_scores[mv] = move_scores.get(mv, 0.0) + weights.get(name, 0.0)

        chosen_move: chess.Move = max(move_scores.items(), key=lambda x: x[1])[0]

        # ----------------------------------------------------------- #
        # 7. Persist history
        # ----------------------------------------------------------- #
        self.history.append((board.copy(), chosen_move, final_regime))

        # ----------------------------------------------------------- #
        # 8. Return move + rich diagnostics
        # ----------------------------------------------------------- #
        diagnostics = {
            "final_regime": final_regime,
            "raw_regime": raw_regime,
            "overridden": overridden,
            "override_reason": rc_reason,
            "opponent_type": opponent_type,
            "features": features,
            "weights": weights,
            "mpc_diag": mpc_diag,
            "module_trace": module_trace
        }
        return chosen_move, diagnostics


# -------------------------------------------------------------------- #
# Builder helper
# -------------------------------------------------------------------- #
def build_mcca_agent() -> MCCAAgent:
    return MCCAAgent()
