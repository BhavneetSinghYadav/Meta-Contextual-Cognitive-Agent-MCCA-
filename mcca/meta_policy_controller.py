import chess

class MetaPolicyController:
    def __init__(self):
        self.previous_regime = None

    def get_strategy_weights(self, regime, state: chess.Board = None):
        # Optional emergency dampening if board is collapsing
        if state:
            collapse_context = self._detect_collapse(state)
            if collapse_context["override"]:
                regime = collapse_context["forced_regime"]

        # Core weights per regime
        weights = self._base_weights(regime)

        # Logic Boost: adapt based on live collapse context
        if state:
            if regime == "deception" and self._king_is_under_threat(state):
                weights["deception"] *= 0.3
                weights["tactical"] += 0.3  # fallback toward clarity

            if self._king_is_central(state):
                weights["positional"] += 0.2
                weights["shaping"] *= 0.5

        self.previous_regime = regime
        return self._normalize(weights)

    def _base_weights(self, regime):
        if regime == "tactical":
            return {
                "tactical": 1.0, "shaping": 0.0,
                "positional": 0.0, "deception": 0.0
            }
        elif regime == "shaping":
            return {
                "tactical": 0.3, "shaping": 0.5,
                "positional": 0.1, "deception": 0.1
            }
        elif regime == "positional":
            return {
                "tactical": 0.2, "shaping": 0.1,
                "positional": 0.6, "deception": 0.1
            }
        elif regime == "deception":
            return {
                "tactical": 0.2, "shaping": 0.1,
                "positional": 0.1, "deception": 0.6
            }
        else:
            return {
                "tactical": 0.6, "shaping": 0.2,
                "positional": 0.1, "deception": 0.1
            }

    def _normalize(self, weights):
        total = sum(weights.values())
        if total == 0:
            return {"tactical": 1.0, "shaping": 0.0, "positional": 0.0, "deception": 0.0}
        return {k: round(v / total, 3) for k, v in weights.items()}

    def _detect_collapse(self, board):
        material_score = self._material_score(board)
        mobility = len(list(board.legal_moves))
        king_threats = self._king_threat_score(board)

        if abs(material_score) >= 6 or king_threats >= 3 or mobility <= 8:
            forced_regime = "tactical" if self._king_is_under_threat(board) else "positional"
            return {"override": True, "forced_regime": forced_regime}
        return {"override": False}

    def _king_is_under_threat(self, board):
        king_sq = board.king(board.turn)
        if king_sq is None:
            return False
        attackers = board.attackers(not board.turn, king_sq)
        return len(attackers) >= 2

    def _king_is_central(self, board):
        king_sq = board.king(board.turn)
        if king_sq in [chess.D4, chess.E4, chess.D5, chess.E5, chess.D3, chess.E3]:
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

    def _king_threat_score(self, board):
        king_sq = board.king(board.turn)
        if king_sq is None:
            return 0
        return len(board.attackers(not board.turn, king_sq))
