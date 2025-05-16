# File: mcca/agent.py

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

    def act(self, state):
        regime = self.regime_detector.predict(state, self.history)
        strategy_weights = self.meta_controller.get_strategy_weights(regime)
        blended_action = self._blend_actions(state, strategy_weights)
        self.history.append((state, blended_action, regime))
        return blended_action

    def _blend_actions(self, state, weights):
        actions = {name: mod.act(state) for name, mod in self.modules.items()}
        blended = sum(weights[name] * actions[name] for name in actions)
        return blended

# Example initialization of MCCAAgent with all modules

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
