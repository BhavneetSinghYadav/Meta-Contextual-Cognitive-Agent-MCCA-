# File: mcca/agent.py

import random
import chess

from mcca.meta_policy_controller import MetaPolicyController
from mcca.regime_detector import RegimeDetector
from mcca.opponent_classifier import OpponentClassifier
from mcca.modules.tactical_module import TacticalModule
from mcca.modules.shaping_module import ShapingModule
from mcca.modules.positional_module import PositionalModule
from mcca.modules.deception_module import DeceptionModule

class MCCAAgent:
    def __init__(self, regime_detector, meta_controller, modules):
        self.regime_detector = regime_detector
        self.meta_controller = meta_controller
        self.modules = modules
        self.opponent_classifier = OpponentClassifier()
        self.history = []

    def act(self, state: chess.Board):
        # 1. Update opponent model if opponent just moved
        if self.history:
            last_board, last_move, _ = self.history[-1]
            if last_board.turn != state.turn:
                self.opponent_classifier.update(last_board, last_move)

        # 2. Classify opponent and predict regime
        opponent_type = self.opponent_classifier.classify()
        regime = self.regime_detector.predict(state, self.history)

        # 3. Override regime based on opponent behavior
        regime = self._bias_regime_with_opponent(regime, opponent_type)

        # 4. Compute adaptive strategy weights
        strategy_weights = self.meta_controller.get_strategy_weights(regime, state)

        # 5. Generate move from weighted module blend
        blended_action = self._blend_actions(state, strategy_weights)

        # 6. Store move trajectory
        self.history.append((state.copy(), blended_action, regime))

        # 7. Return action and diagnostics
        return blended_action, regime, strategy_weights, opponent_type

    def _bias_regime_with_opponent(self, regime, opponent_type):
        if opponent_type == "chaotic":
            return "positional"  # seek structural grounding
        if regime == "tactical":
            if opponent_type == "positional":
                return "deception"  # try bait
        elif regime == "positional":
            if opponent_type == "tactical":
                return "shaping"  # avoid direct conflict
        elif regime == "shaping":
            if opponent_type == "shaping":
                return "positional"  # stabilize
        return regime

    def _blend_actions(self, state: chess.Board, weights):
        legal_moves = list(state.legal_moves)
        if not legal_moves:
            return None

        actions = {}
        for name, module in self.modules.items():
            move = module.act(state)
            if not isinstance(move, chess.Move) or move not in legal_moves:
                move = random.choice(legal_moves)
            actions[name] = move

        # Weighted voting
        move_scores = {}
        for name, move in actions.items():
            move_scores[move] = move_scores.get(move, 0.0) + weights.get(name, 0.0)

        return max(move_scores.items(), key=lambda x: x[1])[0]

# Agent Builder
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
