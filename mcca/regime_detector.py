import chess

class RegimeDetector:
    def __init__(self):
        self.prev_regimes = []

    def predict(self, state: chess.Board, history):
        material_diff = self._material_score(state)
        mobility = len(list(state.legal_moves))
        tension = self._pawn_tension(state)
        king_threat = self._king_exposure(state)
        phase = self._detect_phase(state)
        king_entropy = self._king_oscillation(history)

        # Collapse override: central king + under attack
        if self._emergency_king_threat(state, king_threat):
            return "tactical"

        # Base regime logic
        if king_threat >= 3 or king_entropy >= 2:
            regime = "deception"
        elif tension >= 3 or abs(material_diff) >= 5:
            regime = "positional"
        elif mobility >= 30 and tension == 0:
            regime = "shaping"
        else:
            regime = "tactical"

        # Regime fatigue: reduce stuck-in-loop
        fatigue_penalty = self._regime_fatigue(regime)
        if fatigue_penalty and regime == "deception":
            regime = "tactical"

        # Log regime history
        self.prev_regimes.append(regime)
        if len(self.prev_regimes) > 6:
            self.prev_regimes.pop(0)

        return regime

    def _regime_fatigue(self, regime):
        if self.prev_regimes.count(regime) >= 4:
            return True
        return False

    def _material_score(self, board):
        piece_values = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9
        }
        score = 0
        for piece_type, value in piece_values.items():
            score += value * (
                len(board.pieces(piece_type, chess.WHITE)) -
                len(board.pieces(piece_type, chess.BLACK))
            )
        return score

    def _pawn_tension(self, board):
        tension = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN:
                attackers = board.attackers(not piece.color, square)
                if attackers:
                    tension += 1
        return tension

    def _king_exposure(self, board):
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            king_square = board.king(color)
            if king_square is None:
                continue
            attackers = board.attackers(not color, king_square)
            score += len(attackers)
        return score

    def _detect_phase(self, board):
        move_number = board.fullmove_number
        if move_number <= 10:
            return "opening"
        elif move_number <= 30:
            return "midgame"
        else:
            return "endgame"

    def _king_oscillation(self, history):
        if len(history) < 4:
            return 0
        king_squares = []
        for state, move, _ in history[-4:]:
            king_sq = state.king(state.turn)
            if king_sq:
                king_squares.append(king_sq)
        return len(set(king_squares)) < 3  # High repetition

    def _emergency_king_threat(self, board, king_threat_score):
        king = board.king(board.turn)
        if king in [chess.D4, chess.E4, chess.D5, chess.E5, chess.D3, chess.E3]:
            if king_threat_score >= 2:
                return True
        return False
