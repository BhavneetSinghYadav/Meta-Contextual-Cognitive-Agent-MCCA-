class MetaPolicyController:
    def __init__(self):
        pass

    def get_strategy_weights(self, regime):
        if regime == "tactical":
            return {
                "tactical": 1.0,
                "shaping": 0.0,
                "positional": 0.0,
                "deception": 0.0
            }

        elif regime == "shaping":
            return {
                "tactical": 0.3,
                "shaping": 0.5,
                "positional": 0.1,
                "deception": 0.1
            }

        elif regime == "positional":
            return {
                "tactical": 0.2,
                "shaping": 0.1,
                "positional": 0.6,
                "deception": 0.1
            }

        elif regime == "deception":
            return {
                "tactical": 0.2,
                "shaping": 0.1,
                "positional": 0.1,
                "deception": 0.6
            }

        else:  # fallback
            return {
                "tactical": 0.7,
                "shaping": 0.1,
                "positional": 0.1,
                "deception": 0.1
            }
