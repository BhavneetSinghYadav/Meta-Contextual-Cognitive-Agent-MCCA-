import chess

class MetaPolicyController:
    def __init__(self):
        self.previous_regime = None

    def get_strategy_weights(self, regime, state: chess.Board = None):
        # Emergency override: check collapse
        if state:
            if self._in_collapse(state):
                regime = "tactical" if regime != "deception" else "deception"

        # Save for future regime frustration tracking (optional)
        self.previous_regime = regime

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

    def _in_collapse(self, board: chess.Board) -> bool:
        # Material collapse detection
        material_diff = self._material_score(board)
        if abs(material_diff) >= 5:
            return True

        # King exposed
        for color in [chess.WHITE, chess.BLACK]:
            king = board.king(color)
            if king and len(board.attackers(not color, king)) >= 3:
                return True

        # Legal move collapse (low mobility)
        if len(list(board.legal_moves)) < 10:
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
