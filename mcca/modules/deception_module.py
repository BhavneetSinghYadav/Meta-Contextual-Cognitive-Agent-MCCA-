# File: mcca/modules/deception_module.py
import random
import chess
from mcca.regime_detector import RegimeDetector


class DeceptionModule:
    """
    Bluff-oriented “phantom pressure” generator.

    Returns:
        move (chess.Move)
        diag (dict)
            {
              "deception_score": float,
              "phantom_threats": int,
              "bait_count": int,
              "retreat_flag": bool,
              "king_gap": int,
              "risk": float,        # 0-1
              "suppress": bool,     # true if own king exposed / no bluff value
              "reason": str
            }
    """

    def __init__(self):
        # internal memory: store last 2 deception outcomes (success/fail) for simple regret
        self._fail_tally = 0
        self._lookback = 2

    # ------------------------------------------------------------------ #
    def act(self, board: chess.Board):
        legal = list(board.legal_moves)
        if not legal:
            return None, {"suppress": True, "reason": "no legal moves"}

        checks, attackers = RegimeDetector._tactical_danger_zone(board)
        if board.is_check() or checks >= 2 or attackers >= 3:
            fallback = random.choice(legal)
            return fallback, {"suppress": True, "reason": "danger_zone", "risk": 1.0}

        scored = []
        for mv in legal:
            board.push(mv)
            score, info = self._deception_heuristic(board, mv)
            board.pop()
            scored.append((score, mv, info))

        dec_score, best_move, best_info = max(scored, key=lambda x: x[0])

        # King safety check  -------------------------------------------
        own_color = board.turn
        own_king_sq = board.king(own_color)
        king_threats = len(board.attackers(not own_color, own_king_sq)) if own_king_sq else 0
        suppress = king_threats >= 2 or dec_score < 0.5  # weak bluff or unsafe king

        risk = min((best_info["bait_count"] + king_threats) / 6, 1.0)
        reason = self._build_reason(best_info, suppress, king_threats)

        diag = {
            **best_info,
            "deception_score": round(dec_score, 2),
            "suppress": suppress,
            "risk": round(risk, 2),
            "reason": reason
        }

        return best_move, diag

    # ------------------------------------------------------------------ #
    # INTERNAL HEURISTICS
    # ------------------------------------------------------------------ #
    def _deception_heuristic(self, board: chess.Board, mv: chess.Move):
        """Return (score, info)."""
        opp = not board.turn

        # 1. Phantom threats: squares we attack that they don’t defend
        phantom = sum(
            1 for sq in chess.SQUARES
            if board.is_attacked_by(board.turn, sq) and
               not board.is_attacked_by(opp, sq)
        )

        # 2. Hanging bait: our pieces now apparently undefended
        bait = sum(
            1
            for sq in chess.SQUARES
            if (piece := board.piece_at(sq)) and piece.color == board.turn
            if (board.attackers(opp, sq) and not board.attackers(board.turn, sq))
        )

        # 3. Retreat flag (piece moves backwards relative to own side)
        retreat = (mv.from_square // 8 > mv.to_square // 8) if board.turn == chess.WHITE else (
            mv.from_square // 8 < mv.to_square // 8)

        # 4. King gap (distance between kings)
        wk, bk = board.king(chess.WHITE), board.king(chess.BLACK)
        king_gap = 0
        if wk and bk:
            king_gap = abs((wk % 8) - (bk % 8)) + abs((wk // 8) - (bk // 8))

        # 5. Aggregate deception score
        score = (0.7 * bait +
                 0.5 * phantom +
                 (0.4 if retreat else 0.0) +
                 0.3 * (king_gap >= 5) +
                 random.uniform(0, 0.25))

        info = {
            "phantom_threats": phantom,
            "bait_count": bait,
            "retreat_flag": retreat,
            "king_gap": king_gap
        }
        return score, info

    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_reason(info, suppress, threats):
        parts = []
        if suppress:
            parts.append(f"king_threats={threats}")
        if info["bait_count"]:
            parts.append(f"bait={info['bait_count']}")
        if info["phantom_threats"]:
            parts.append(f"phantom={info['phantom_threats']}")
        if info["retreat_flag"]:
            parts.append("retreat")
        return "; ".join(parts) if parts else "bluff attempt"
