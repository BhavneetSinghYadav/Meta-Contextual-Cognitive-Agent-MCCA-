import chess

class RegimeDetector:
    def __init__(self):
        self.prev_regimes = []
        self.fatigue_threshold = 3  # max repetitions before override
        self.last_eval = None
        self.last_check = False

    def predict(self, board: chess.Board, history, last_eval=None):
        """
        Predicts the current regime based on:
        - Board state features
        - Tactical threats (check)
        - Regime fatigue
        - King exposure
        - Eval drops (if provided)
        """
        # Store for internal override logic
        self.last_eval = last_eval
        self.last_check = board.is_check()

        # 1. Compute symbolic signals
        material_balance = self._material_score(board)
        tension = self._pawn_tension(board)
        mobility = len(list(board.legal_moves))
        king_exposure = self._king_threat(board)
        eval_danger = self._eval_collapse(last_eval)

        # 2. Core regime heuristics
        if self.last_check or king_exposure >= 2 or eval_danger:
            regime = "tactical"
        elif tension >= 3 or abs(material_balance) >= 5:
            regime = "positional"
        elif mobility >= 30 and tension == 0:
            regime = "shaping"
        else:
            regime = "deception"

        # 3. Regime fatigue override
        if self._fatigue_detected(regime):
            regime = "tactical"

        # 4. Update regime memory
        self.prev_regimes.append(regime)
        if len(self.prev_regimes) > 5:
            self.prev_regimes.pop(0)

        return regime

    def _fatigue_detected(self, regime):
        if len(self.prev_regimes) < self.fatigue_threshold:
            return False
        return all(r == regime for r in self.prev_regimes[-self.fatigue_threshold:])

    def _material_score(self, board):
        piece_values = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9
        }
        score = 0
        for piece_type, val in piece_values.items():
            score += val * (
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

    def _king_threat(self, board):
        # Count direct threats to both kings
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            ksq = board.king(color)
            if ksq:
                attackers = board.attackers(not color, ksq)
                score += len(attackers)
        return score

    def _eval_collapse(self, eval_score):
        """
        If eval_score drops significantly (>= 150 centipawns) from a previously stored eval,
        trigger a collapse warning.
        """
        if eval_score is None or self.last_eval is None:
            return False
        try:
            delta = self.last_eval.relative.score(mate_score=10000) - eval_score.relative.score(mate_score=10000)
            return delta >= 150  # 1.5 pawn drop
        except:
            return False
