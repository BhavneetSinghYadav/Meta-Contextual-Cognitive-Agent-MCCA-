# File: mcca/agent.py

import random
import chess

from mcca.meta_policy_controller import MetaPolicyController
from mcca.regime_detector import RegimeDetector
from mcca.modules.tactical_module import TacticalModule
from mcca.modules.shaping_module import ShapingModule
from mcca.modules.positional_module import PositionalModule
from mcca.modules.deception_module import DeceptionModule

class MCCAAgent:
    def __init__(self, regime_detector, meta_controller, modules):
        self.regime_detector = regime_detector
        self.meta_controller = meta_controller
        self.modules = modules
        self.history = []

    def act(self, state: chess.Board):
        # 1. Predict regime based on board + history
        regime = self.regime_detector.predict(state, self.history)

        # 2. Fetch module weights, now collapse-aware
        strategy_weights = self.meta_controller.get_strategy_weights(regime, state)

        # 3. Blend module outputs
        blended_action = self._blend_actions(state, strategy_weights)

        # 4. Record full state-action-regime tuple
        self.history.append((state.copy(), blended_action, regime))

        # 5. Return move + trace info for logging
        return blended_action, regime, strategy_weights

    def _blend_actions(self, state: chess.Board, weights):
        legal_moves = list(state.legal_moves)
        if not legal_moves:
            return None  # Stalemate or checkmate

        actions = {}
        for name, module in self.modules.items():
            move = module.act(state)

            if not isinstance(move, chess.Move) or move not in legal_moves:
                move = random.choice(legal_moves)

            actions[name] = move

        # Weighted vote aggregation
        move_scores = {}
        for name, move in actions.items():
            move_scores[move] = move_scores.get(move, 0.0) + weights.get(name, 0.0)

        # Select move with highest composite score
        best_move = max(move_scores.items(), key=lambda x: x[1])[0]
        return best_move

# Builder
def build_mcca_agent():
    modules = {
        "tactical": TacticalModule(),
        "shaping": ShapingModule(),
        "positional": PositionalModule(),
        "deception": DeceptionModule()
    }
    return MCCAAgent(
        regime_detector=RegimeDetector(),
        meta_controller=MetaPolicyController(),
        modules=modules
    )
