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