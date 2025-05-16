class MetaPolicyController:
    def __init__(self):
        pass

    def get_strategy_weights(self, regime):
        return {"tactical": 1.0, "shaping": 0.0, "positional": 0.0, "deception": 0.0}