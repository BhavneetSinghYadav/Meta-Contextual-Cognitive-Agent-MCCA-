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
        regime = self.regime_detector.predict(state, self.history)
        strategy_weights = self.meta_controller.get_strategy_weights(regime)
        blended_action = self._blend_actions(state, strategy_weights)

        self.history.append((state.copy(), blended_action, regime))

        # Now returns action + debug data
        return blended_action, regime, strategy_weights

    def _blend_actions(self, state: chess.Board, weights):
        legal_moves = list(state.legal_moves)

        if not legal_moves:
            return None  # No legal move possible (checkmate or stalemate)

        actions = {}
        for name, module in self.modules.items():
            move = module.act(state)

            # Fallback if module fails or gives illegal move
            if not isinstance(move, chess.Move) or move not in legal_moves:
                move = random.choice(legal_moves)

            actions[name] = move

        # Weighted voting by module
        move_scores = {}
        for name, move in actions.items():
            move_scores[move] = move_scores.get(move, 0.0) + weights.get(name, 0.0)

        # Select move with highest score
        best_move = max(move_scores.items(), key=lambda x: x[1])[0]
        return best_move

# Agent builder
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
