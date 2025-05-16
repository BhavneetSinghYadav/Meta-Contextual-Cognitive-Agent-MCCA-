import chess

class RegimeDetector:
    def __init__(self):
        self.collapse_threshold_material = 5
        self.collapse_mobility_gap = 15
        self.phase_move_cutoffs = {"opening": 10, "midgame": 30}

    def predict(self, state: chess.Board, history):
        material_diff = self._material_score(state)
        mobility = len(list(state.legal_moves))
        tension = self._pawn_tension(state)
        king_threat = self._king_exposure(state)
        phase = self._detect_phase(state)

        # Collapse override logic
        if self._in_collapse(state, material_diff, mobility, king_threat):
            return "tactical" if phase == "endgame" else "deception"

        # Regime based on phase + signals
        if king_threat >= 2:
            return "deception"
        elif tension >= 3 or abs(material_diff) >= 5:
            return "positional"
        elif mobility >= 30 and tension <= 1:
            return "shaping"
        else:
            return "tactical"

    def _detect_phase(self, board: chess.Board):
        move_number = board.fullmove_number
        if move_number <= self.phase_move_cutoffs["opening"]:
            return "opening"
        elif move_number <= self.phase_move_cutoffs["midgame"]:
            return "midgame"
        else:
            return "endgame"

    def _in_collapse(self, board: chess.Board, material_diff, mobility, king_threat):
        # Material collapse
        if abs(material_diff) >= self.collapse_threshold_material:
            return True
        # King under heavy fire
        if king_threat >= 3:
            return True
        # Mobility collapse compared to opponent
        if board.turn:  # White's turn
            enemy_mobility = len(list(board.legal_moves))
        else:
            board.push(chess.Move.null())
            enemy_mobility = len(list(board.legal_moves))
            board.pop()
        if enemy_mobility - mobility > self.collapse_mobility_gap:
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
