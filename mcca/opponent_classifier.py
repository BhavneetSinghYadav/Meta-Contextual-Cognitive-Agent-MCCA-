class OpponentClassifier:
    def __init__(self):
        self.history = []

    def update(self, state, move):
        self.history.append((state, move))

    def classify(self):
        # Naive heuristic: if behavior is deep-calculated, it's tactical
        if len(self.history) < 5:
            return "unknown"
        elif all(state.turn == move.to_square % 2 for state, move in self.history[-3:]):
            return "tactical"
        else:
            return "shaping"
