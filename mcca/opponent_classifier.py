import chess

class OpponentClassifier:
    def __init__(self):
        self.history = []

    def update(self, state: chess.Board, move: chess.Move):
        self.history.append((state.copy(), move))
        if len(self.history) > 12:
            self.history.pop(0)  # limit memory

    def classify(self):
        if len(self.history) < 6:
            return "unknown"

        states = [s for s, _ in self.history[-6:]]
        moves = [m for _, m in self.history[-6:]]

        scores = {
            "tactical": self._tactical_aggression(states, moves),
            "shaping": self._entropy_induction(states, moves),
            "positional": self._quiet_repositioning(states, moves)
        }

        # Optional chaotic label if conflict between high entropy and attack rate
        if scores["shaping"] >= 4 and scores["tactical"] >= 4:
            return "chaotic"

        return max(scores.items(), key=lambda x: x[1])[0]

    def _tactical_aggression(self, states, moves):
        score = 0
        for s, m in zip(states, moves):
            if s.is_capture(m):
                score += 1.5
            if s.gives_check(m):
                score += 1.2
            if m.promotion:
                score += 1.0
        return round(score, 2)

    def _entropy_induction(self, states, moves):
        score = 0
        for s, m in zip(states, moves):
            if chess.square_file(m.from_square) in [0, 7]:
                score += 1.0
            if s.is_en_passant(m):
                score += 1.0
            piece = s.piece_at(m.from_square)
            if piece and piece.piece_type == chess.PAWN and abs(chess.square_file(m.to_square) - chess.square_file(m.from_square)) >= 2:
                score += 0.5
        return round(score, 2)

    def _quiet_repositioning(self, states, moves):
        score = 0
        for s, m in zip(states, moves):
            piece = s.piece_at(m.from_square)
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK]:
                if not s.is_capture(m) and not s.gives_check(m):
                    score += 1.0
        return round(score, 2)
