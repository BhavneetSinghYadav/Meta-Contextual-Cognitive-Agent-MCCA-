import chess

class OpponentClassifier:
    def __init__(self):
        self.history = []

    def update(self, state: chess.Board, move: chess.Move):
        # Save a copy of board and move made
        self.history.append((state.copy(), move))

    def classify(self):
        if len(self.history) < 6:
            return "unknown"

        # Extract recent context
        last_states = [state for state, _ in self.history[-5:]]
        last_moves = [move for _, move in self.history[-5:]]

        # Heuristic scores
        tactical_score = self._tactical_aggression(last_states, last_moves)
        shaping_score = self._entropy_induction(last_states, last_moves)
        positional_score = self._long_term_buildup(last_states, last_moves)

        # Final classification
        scores = {
            "tactical": tactical_score,
            "shaping": shaping_score,
            "positional": positional_score
        }

        best_type = max(scores.items(), key=lambda x: x[1])[0]
        return best_type

    def _tactical_aggression(self, states, moves):
        score = 0
        for state, move in zip(states, moves):
            # Piece capture or king pursuit
            if state.is_capture(move):
                score += 1.5
            if state.gives_check(move):
                score += 1.0
            if move.promotion:
                score += 1.0
        return score

    def _entropy_induction(self, states, moves):
        score = 0
        for state, move in zip(states, moves):
            # Central pawns sacrificed or non-standard flank pushes
            if move.from_square in [chess.D2, chess.E2, chess.D7, chess.E7] and not state.is_capture(move):
                score -= 1.0  # conservative
            elif chess.square_file(move.from_square) in [0, 7]:
                score += 1.0  # entropy by flanking
            elif state.is_en_passant(move):
                score += 1.0
        return score

    def _long_term_buildup(self, states, moves):
        score = 0
        for state, move in zip(states, moves):
            piece = state.piece_at(move.from_square)
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK]:
                # Repositioning non-pawns repeatedly
                score += 1.0
            if not state.is_capture(move) and not state.gives_check(move):
                score += 0.5  # positional quiet move
        return score
