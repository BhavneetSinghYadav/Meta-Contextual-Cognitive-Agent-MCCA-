# File: mcca/modules/tactical_module.py
import random
import chess
import chess.engine


class TacticalModule:
    """
    Stock-fish-backed tactical oracle with symbolic diagnostics.

    Returns:
        move (chess.Move)                    - the engine’s best move (or legal fallback)
        diag (dict)                          - rich diagnostic bundle for the agent loop:
            {
                "score_cp": int | None,      # centipawn score (from White’s POV)
                "mate_score": int | None,    # mate in N (±N, None if absent)
                "eval_delta": int | None,    # Δcp vs previous call (None on first call)
                "check_after": bool,         # does chosen pv give check immediately?
                "suggest_override": bool,    # flag: regime should switch to tactical
                "risk": float,               # heuristic risk metric (0-1)
                "suppress": bool,            # always False for tactical module
                "reason": str                # human-readable explanation
            }
    """

    def __init__(self, stockfish_path: str = "/usr/games/stockfish", depth: int = 10):
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        self.depth = depth
        self._prev_cp = None  # stores previous centipawn score for Δ computation

    # --------------------------------------------------------------------- #
    # PUBLIC API
    # --------------------------------------------------------------------- #
    def act(self, board: chess.Board):
        """Return best tactical move + diagnostic bundle."""
        best_move, score_obj = self._analyse(board)

        # ----------------------------------------------------------------
        # Build diagnostics
        # ----------------------------------------------------------------
        score_cp, mate_score = self._extract_score(score_obj)
        eval_delta = None
        if score_cp is not None and self._prev_cp is not None:
            eval_delta = score_cp - self._prev_cp

        self._prev_cp = score_cp  # update memory

        check_after = self._check_after(board, best_move)
        suggest_override = bool(check_after or                     # we give check
                                (mate_score is not None) or        # mate detected
                                (eval_delta is not None and eval_delta <= -150))  # collapse

        # simple risk metric: worse eval (< 0) or big drop → high risk
        risk = 0.0
        if score_cp is not None:
            if score_cp < 0:
                risk += min(abs(score_cp) / 400, 1.0)  # cap at 1.0
        if eval_delta is not None and eval_delta < 0:
            risk += min(abs(eval_delta) / 400, 1.0)
        risk = round(min(risk, 1.0), 2)

        diag = {
            "score_cp": score_cp,
            "mate_score": mate_score,
            "eval_delta": eval_delta,
            "check_after": check_after,
            "suggest_override": suggest_override,
            "risk": risk,
            "suppress": False,            # tactical module is never suppressed
            "reason": self._build_reason(score_cp, mate_score, check_after, eval_delta)
        }
        return best_move, diag

    def evaluate(self, board: chess.Board):
        """Light-weight evaluation only (returns {'cp': int|None, 'mate': int|None})."""
        _, score_obj = self._analyse(board)
        return {"cp": *self._extract_score(score_obj)}

    def close(self):
        self.engine.quit()

    # --------------------------------------------------------------------- #
    # INTERNAL HELPERS
    # --------------------------------------------------------------------- #
    def _analyse(self, board):
        """Run Stockfish analysis, fallback gracefully on failure."""
        try:
            result = self.engine.analyse(board, chess.engine.Limit(depth=self.depth))
            best_move = result.get("pv", [None])[0]
            score_obj = result.get("score", None)
            if best_move is None:
                best_move = random.choice(list(board.legal_moves))
            return best_move, score_obj
        except Exception as e:
            print(f"[TacticalModule] Engine failure: {e}")
            fallback = random.choice(list(board.legal_moves))
            return fallback, None

    @staticmethod
    def _extract_score(score_obj):
        """Convert Stockfish score object to (centipawn, mate)."""
        if score_obj is None:
            return None, None
        try:
            if score_obj.is_mate():
                return None, score_obj.mate()
            return score_obj.score(), None  # centipawns
        except Exception:
            return None, None

    @staticmethod
    def _check_after(board, move):
        """Whether the principal variation’s first move gives check."""
        try:
            board.push(move)
            is_check = board.is_check()
            board.pop()
            return is_check
        except Exception:
            return False

    @staticmethod
    def _build_reason(cp, mate, check_after, delta):
        parts = []
        if check_after:
            parts.append("immediate check")
        if mate is not None:
            parts.append(f"mate in {abs(mate)} ({'+' if mate > 0 else '-'})")
        if delta is not None and delta <= -150:
            parts.append("eval collapse")
        if not parts:
            return "normal tactical best-move output"
        return "; ".join(parts)
