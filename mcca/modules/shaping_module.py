# File: mcca/modules/shaping_module.py
import random
import chess


class ShapingModule:
    """
    Asymmetry-seeking “entropy” generator.

    Returns:
        move  (chess.Move) - selected shaping move (or fallback)
        diag  (dict)       - symbolic diagnostics:
            {
              "entropy_score": float,
              "mobility": int,
              "king_distance": int,
              "open_files": int,
              "flank_pressure": bool,
              "suppress": bool,        # advise controller to down-weight if True
              "risk": float,           # 0-1 heuristic risk (king still in centre, etc.)
              "reason": str
            }
    """

    def __init__(self):
        # suppression threshold when own king is exposed
        self.king_exposure_cutoff = 3

    # ------------------------------------------------------------------ #
    # PUBLIC API
    # ------------------------------------------------------------------ #
    def act(self, board: chess.Board):
        moves = list(board.legal_moves)
        if not moves:
            return None, {"suppress": True, "reason": "no legal moves"}

        scored = []
        for mv in moves:
            board.push(mv)
            entropy, info = self._entropy_heuristic(board)
            board.pop()
            scored.append((entropy, mv, info))

        entropy_best, best_move, best_info = max(scored, key=lambda x: x[0])

        # KING-SAFETY RISK  ------------------------------------------------
        own_color = board.turn
        own_king_sq = board.king(own_color)
        king_threats = len(board.attackers(not own_color, own_king_sq)) if own_king_sq else 0
        suppress_flag = king_threats >= self.king_exposure_cutoff

        # assemble diagnostics
        diag = {
            **best_info,
            "entropy_score": round(entropy_best, 2),
            "suppress": suppress_flag,
            "risk": self._compute_risk(best_info, king_threats),
            "reason": self._build_reason(best_info, suppress_flag, king_threats)
        }

        return best_move, diag

    # ------------------------------------------------------------------ #
    # INTERNAL HELPERS
    # ------------------------------------------------------------------ #
    def _entropy_heuristic(self, board: chess.Board):
        """Compute entropy proxy and sub-metrics."""
        mobility = len(list(board.legal_moves))

        # king distance
        w_k, b_k = board.king(chess.WHITE), board.king(chess.BLACK)
        king_distance = 0
        if w_k is not None and b_k is not None:
            king_distance = abs((w_k % 8) - (b_k % 8)) + abs((w_k // 8) - (b_k // 8))

        # open files (no pawns blocking)
        open_files = sum(
            1
            for file in range(8)
            if not any(
                board.piece_at(chess.square(file, rank))  # pawn or any piece
                and board.piece_at(chess.square(file, rank)).piece_type == chess.PAWN
                for rank in range(8)
            )
        )

        # centre pressure
        centre_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        centre_pressure = sum(
            1 for sq in centre_squares
            if board.is_attacked_by(chess.WHITE, sq) or board.is_attacked_by(chess.BLACK, sq)
        )

        # flank pressure flag (rook/queen on semi-open a/h file)
        flank_pressure = any(
            board.piece_at(sq)
            and board.piece_at(sq).piece_type in (chess.ROOK, chess.QUEEN)
            for sq in [chess.A1, chess.A8, chess.H1, chess.H8]
        )

        # pawn symmetry penalty
        pawn_symmetry = sum(
            1
            for file in range(8)
            if board.piece_at(chess.square(file, 1)) and board.piece_at(chess.square(file, 6))
        )

        # ENTROPY SCORE (tuned weights)
        entropy = (
            1.3 * mobility +
            0.9 * king_distance +
            0.8 * open_files +
            0.7 * centre_pressure -
            0.6 * pawn_symmetry
        )

        info = {
            "mobility": mobility,
            "king_distance": king_distance,
            "open_files": open_files,
            "centre_pressure": centre_pressure,
            "flank_pressure": flank_pressure
        }
        return entropy, info

    @staticmethod
    def _compute_risk(info, king_threats):
        """Simple 0-1 risk metric."""
        risk = 0.0
        if king_threats:
            risk += min(king_threats / 4, 1.0)
        if info["open_files"] >= 5:
            risk += 0.2
        if info["flank_pressure"]:
            risk += 0.1
        return round(min(risk, 1.0), 2)

    @staticmethod
    def _build_reason(info, suppress, threats):
        parts = []
        if suppress:
            parts.append(f"king threatened x{threats}")
        parts.append(f"mobility={info['mobility']}")
        parts.append(f"open_files={info['open_files']}")
        if info["flank_pressure"]:
            parts.append("flank_pressure")
        return "; ".join(parts)
