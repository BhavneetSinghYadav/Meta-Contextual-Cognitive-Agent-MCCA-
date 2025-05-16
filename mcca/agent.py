# File: mcca/agent.py
from __future__ import annotations

import random
import chess
from typing import Dict, Any, Tuple

from mcca.meta_policy_controller import MetaPolicyController
from mcca.regime_detector import RegimeDetector
from mcca.regime_changer import RegimeChanger
from mcca.opponent_classifier import OpponentClassifier

from mcca.modules.tactical_module import TacticalModule
from mcca.modules.shaping_module import ShapingModule
from mcca.modules.positional_module import PositionalModule
from mcca.modules.deception_module import DeceptionModule


class MCCAAgent:
    """
    MCCA v3.2 — full symbolic pipeline
    ----------------------------------
        RegimeDetector  → RegimeChanger → MetaPolicyController
              |                |                 |
           (features)       (override)         (weights)
              |                |                 |
        --------------  MODULE TRACE  ---------------
              |          (diag per module)
              |                |                 |
           Module Blend   ←  Suppress / Risk  ←  Controller
    """

    # --------------------------------------------------------------- #
    def __init__(
        self,
        regime_detector: RegimeDetector,
        regime_changer: RegimeChanger,
        meta_controller: MetaPolicyController,
        modules: Dict[str, Any],
    ):
        self.detector = regime_detector
        self.changer = regime_changer
        self.controller = meta_controller
        self.modules = modules

        self.opponent_classifier = OpponentClassifier()
        self.history: list = []    # [(board, move, regime, weights)]

    # --------------------------------------------------------------- #
    def act(self, board: chess.Board) -> Tuple[chess.Move, Dict[str, Any]]:
        """
        Main decision loop.

        Returns
        -------
        move          : chess.Move
        diagnostics   : dict (full symbolic trace & reasoning)
        """
        # ----------------------------------------------------------- #
        # 1. Update opponent model (if opponent just moved)
        # ----------------------------------------------------------- #
        if self.history:
            last_board, last_move, _reg, _w = self.history[-1]
            if last_board.turn != board.turn:
                self.opponent_classifier.update(last_board, last_move)
        opponent_type = self.opponent_classifier.classify()

        # ----------------------------------------------------------- #
        # 2. Pre–evaluation (centipawn) using tactical engine
        #    – cheap 1-depth evaluation, reused later for features
        # ----------------------------------------------------------- #
        eval_obj = None
        try:
            eval_obj = self.modules["tactical"].evaluate(board)
            eval_obj = eval_obj if isinstance(eval_obj, dict) else None
        except Exception:
            eval_obj = None

        # ----------------------------------------------------------- #
        # 3. Regime Detection  →  raw suggestion + features
        # ----------------------------------------------------------- #
        raw_regime, features = self.detector.predict(
            board, self.history, eval_obj
        )

        # ----------------------------------------------------------- #
        # 4. Module calls — generate candidate moves & diagnostics
        # ----------------------------------------------------------- #
        module_trace: Dict[str, Dict[str, Any]] = {}
        module_moves: Dict[str, chess.Move] = {}

        legal = list(board.legal_moves)
        for name, module in self.modules.items():
            mv, diag = module.act(board)
            # engine failure fallback
            if mv not in legal:
                mv = random.choice(legal)
                diag["reason"] += " | fallback"
            module_trace[name] = diag
            module_moves[name] = mv

        # ----------------------------------------------------------- #
        # 5. Regime Changer  →  final regime (may override)
        # ----------------------------------------------------------- #
        final_regime, overridden, reg_reason = self.changer.decide(
            raw_regime,
            features,
            opponent_type,
            module_trace
        )

        # ----------------------------------------------------------- #
        # 6. Meta-policy blending weights
        # ----------------------------------------------------------- #
        weights, ctrl_diag = self.controller.get_strategy_weights(
            final_regime,
            board,
            features,
            self.history,
            opponent_type,
            module_trace
        )

        # ----------------------------------------------------------- #
        # 7. Blended move selection
        # ----------------------------------------------------------- #
        move = self._blend_moves(module_moves, weights, legal)

        # ----------------------------------------------------------- #
        # 8. Record history
        # ----------------------------------------------------------- #
        self.history.append((board.copy(), move, final_regime, weights))

        # ----------------------------------------------------------- #
        # 9. Assemble diagnostics
        # ----------------------------------------------------------- #
        diagnostics = {
            "move": move.uci(),
            "raw_regime": raw_regime,
            "final_regime": final_regime,
            "regime_override": overridden,
            "regime_reason":
