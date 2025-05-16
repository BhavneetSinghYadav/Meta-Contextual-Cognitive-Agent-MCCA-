# File: mcca/modules/positional_module.py
import random
import chess


class PositionalModule:
    """
    Strategic “structure & space” optimiser.

    Returns:
        move  (chess.Move)
        diag  (dict)   symbolic diagnostics
            {
              "positional_score": float,
              "centre_pressure": float,
              "dev_score": float,
              "pawn_penalty": float,
              "king_safety": float,
              "suppress": bool,   # true if king unsafe or eval falling
              "risk": float,      # heuristic 0-1
              "reason": str
            }
    """

    def __init__(self):
        self.center = [chess.D4, chess.E4, chess.D5, chess.E5]
        self.ext_center = [chess.C4, chess.F4, chess.C5, chess.F5]
        self.prev_score = None  # for Δ evaluation

    # ---------------------------------------------------------------- #
    # PUBLIC API
    # ---------------------------------------------------------------- #
    def act(self, board: chess.Board):
        legal = list(board.legal_moves)
        if not legal:
            return None, {"suppress": True, "reason": "stalemate/zugzwang"}

        scored = []
        for mv in legal:
            board.push(mv)
            score, info = self._positional_heuristic(board)
            board.pop()
            scored.append((score, mv, info))

        best_score, best_move, best_info = max(scored, key=lambda x: x[0])

        # King safety suppression
        own_color = board.turn
        king_sq = board.king(own_color)
        king_exposure = len(board.attackers(not own_color, king_sq)) if king_sq else 0
        suppress = king_exposure >= 3

        risk = min(max(-best_score, 0) / 8, 1.0)  # rough inverse of score

        diag = {
            **best_info,
            "positional_score": round(best_score, 2),
            "suppress": suppress,
            "risk": round(risk, 2),
            "reason": self._build_reason(best_info, suppress, king_exposure)
        }
        self.prev_score = best_score
        return best_move, diag

    # ---------------------------------------------------------------- #
    # INTERNAL SCORING
    # ---------------------------------------------------------------- #
    def _positional_heuristic(self, board: chess.Board):
        """Return (score, info_dict)."""
        # 1. Centre control ------------------------------------------------
        centre_press = sum(
            1 for sq in self.center
            if board.is_attacked_by(board.turn, sq)
        )
        ext_press = 0.5 * sum(
            1 for sq in self.ext_center
            if board.is_attacked_by(board.turn, sq)
        )

        # 2. Piece development -------------------------------------------
        dev_score = 0.0
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if not p or p.color != board.turn:
                continue
            rank = sq // 8
            file = sq % 8
            if p.piece_type == chess.KNIGHT and rank >= 2:
                dev_score += 0.4
            elif p.piece_type == chess.BISHOP and rank >= 2:
                dev_score += 0.3
            elif p.piece_type == chess.ROOK and file in (3, 4):
                dev_score += 0.3
            elif p.piece_type == chess.QUEEN and rank >= 2:
                dev_score += 0.2
            elif p.piece_type == chess.KING:
                if sq in (chess.G1, chess.C1, chess.G8, chess.C8):
                    dev_score += 0.6  # castled
                elif rank in (3, 4):
                    dev_score -= 0.8  # exposed king

        # 3. Pawn structure ----------------------------------------------
        pawn_penalty = self._pawn_structure_penalty(board)

        # 4. Aggregate score ---------------------------------------------
        score = (1.2 * centre_press +
                 ext_press +
                 dev_score -
                 pawn_penalty)

        info = {
            "centre_pressure": centre_press + ext_press,
            "dev_score": round(dev_score, 2),
            "pawn_penalty": round(pawn_penalty, 2),
            "king_safety": round(-dev_score if dev_score < 0 else 0, 2)
        }
        return score, info

    # ---------------------------------------------------------------- #
    def _pawn_structure_penalty(self, board: chess.Board):
        pawns = list(board.pieces(chess.PAWN, board.turn))
        file_counts = {}
        for sq in pawns:
            file_counts[sq % 8] = file_counts.get(sq % 8, 0) + 1

        penalty = 0.0
        for file, cnt in file_counts.items():
            if cnt >= 2:
                penalty += 0.3 * (cnt - 1)  # doubled
            # isolated
            neighbors = file_counts.get(file - 1, 0) + file_counts.get(file + 1, 0)
            if cnt == 1 and neighbors == 0:
                penalty += 0.4
        return penalty

    # ---------------------------------------------------------------- #
    @staticmethod
    def _build_reason(info, suppress, king_threats):
        parts = []
        if suppress:
            parts.append(f"king_threats={king_threats}")
        parts.append(f"Centre={info['centre_pressure']}")
        parts.append(f"Dev={info['dev_score']}")
        parts.append(f"PawnPenalty={info['pawn_penalty']}")
        return "; ".join(parts)
