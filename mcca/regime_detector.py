import chess

class RegimeDetector:
    def __init__(self):
        pass

    def predict(self, state: chess.Board, history):
        # Count material
        material_diff = self._material_score(state)
        # Count mobility
        mobility = len(list(state.legal_moves))
        # Check piece imbalance
        tension = self._pawn_tension(state)
        # Check for direct king threat
        deception = self._king_exposure(state)

        # Rules
        if deception >= 2:
            return "deception"
        elif tension >= 3 or abs(material_diff) >= 5:
            return "positional"
        elif mobility >= 30 and tension == 0:
            return "shaping"
        else:
            return "tactical"

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
