# File: mcca/regime_detector.py
"""
RegimeDetector v3.2
-------------------
Pure *symbolic signal extractor* plus *raw regime proposer*.

Responsibilities
----------------
1.  extract_features(board, history, eval_obj)
      -> returns rich symbolic feature vector (dict)

2.  predict(board, history, eval_obj)
      -> (raw_regime_suggestion, features)

NO override / fatigue / suppression logic lives here now!
That work belongs to `RegimeChanger`.
"""

from __future__ import annotations
import chess
from typing import Dict, Any, Tuple, List


class RegimeDetector:
    # ---------------------------- INIT -------------------------------- #
    def __init__(self):
        self.prev_cp: int | None = None         # previous centipawn score
        self.prev_regimes: List[str] = []       # history (for fatigue feature only)
        self.fatigue_window = 4                 # length for fatigue feature

        # static squares
        self._centre = [chess.D4, chess.E4, chess.D5, chess.E5]

    # ---------------------------- PUBLIC ------------------------------ #
    # 1. FEATURE EXTRACTION
    def extract_features(
        self,
        board: chess.Board,
        history: list,
        eval_obj: chess.engine.PovScore | None = None
    ) -> Dict[str, Any]:
        """Return symbolic feature dict (absolute values, no override)."""
        mat = self._material_diff(board)
        mobility = len(list(board.legal_moves))
        tension = self._pawn_tension(board)
        king_exposure = self._king_exposure(board)
        centre_ctrl = self._centre_control(board)
        symmetry = self._pawn_symmetry(board)
        in_check = board.is_check()
        danger_checks, danger_attackers = self._tactical_danger_zone(board)

        # evaluation handling
        eval_cp = self._extract_cp(eval_obj)
        eval_delta = None
        if eval_cp is not None and self.prev_cp is not None:
            eval_delta = eval_cp - self.prev_cp
        self.prev_cp = eval_cp  # update memory

        # fatigue feature: same regime suggested N times
        fatigue_risk = False
        if len(self.prev_regimes) >= self.fatigue_window:
            fatigue_risk = len(set(self.prev_regimes[-self.fatigue_window:])) == 1

        return {
            "material_diff": mat,
            "mobility_score": mobility,
            "pawn_tension_count": tension,
            "king_exposure_score": king_exposure,
            "center_control_score": centre_ctrl,
            "symmetry_score": symmetry,
            "eval_score": eval_cp,
            "eval_delta": eval_delta,
            "in_check": in_check,
            "fatigue_risk": fatigue_risk,
            "danger_checks": danger_checks,
            "danger_attackers": danger_attackers
        }

    # 2. REGIME PROPOSAL
    def predict(
        self,
        board: chess.Board,
        history: list,
        eval_obj: chess.engine.PovScore | None = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Returns (raw_regime_suggestion, features_dict).
        Down-stream RegimeChanger may override.
        """
        feats = self.extract_features(board, history, eval_obj)

        # immediate tactical danger detection
        if feats["danger_checks"] >= 2 or feats["danger_attackers"] >= 3:
            regime = "tactical"
            self.prev_regimes.append(regime)
            if len(self.prev_regimes) > 8:
                self.prev_regimes.pop(0)
            return regime, feats

        # --- simple heuristic mapping --------------------------------- #
        if feats["in_check"] or feats["king_exposure_score"] >= 2 or \
           (feats["eval_delta"] is not None and feats["eval_delta"] <= -150):
            regime = "tactical"
        elif feats["pawn_tension_count"] >= 3 or abs(feats["material_diff"]) >= 5:
            regime = "positional"
        elif feats["mobility_score"] >= 30 and feats["pawn_tension_count"] == 0 and \
                feats["symmetry_score"] < 0.5:
            regime = "shaping"
        else:
            regime = "deception"

        # store for fatigue feature (but not used for override here)
        self.prev_regimes.append(regime)
        if len(self.prev_regimes) > 8:
            self.prev_regimes.pop(0)

        return regime, feats

    # --------------------------- HELPERS ------------------------------ #
    @staticmethod
    def _extract_cp(score_obj):
        """Convert Stockfish PovScore/dict/int → centipawns (int) or None."""
        if score_obj is None:
            return None
        # direct int passed
        if isinstance(score_obj, (int, float)):
            return int(score_obj)
        # dict from TacticalModule.evaluate()
        if isinstance(score_obj, dict):
            if score_obj.get("mate") is not None:
                return 10000 if score_obj["mate"] > 0 else -10000
            return score_obj.get("cp")
        try:
            if score_obj.is_mate():
                # treat mate as large positive/negative (clip to ±10000)
                return 10000 if score_obj.mate() > 0 else -10000
            return score_obj.score()
        except Exception:
            return None

    @staticmethod
    def _material_diff(board: chess.Board) -> int:
        val = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
               chess.ROOK: 5, chess.QUEEN: 9}
        diff = 0
        for p, v in val.items():
            diff += v * (len(board.pieces(p, chess.WHITE)) -
                         len(board.pieces(p, chess.BLACK)))
        return diff

    @staticmethod
    def _pawn_tension(board: chess.Board) -> int:
        tension = 0
        for sq in chess.SQUARES:
            pc = board.piece_at(sq)
            if pc and pc.piece_type == chess.PAWN:
                if board.attackers(not pc.color, sq):
                    tension += 1
        return tension

    @staticmethod
    def _king_exposure(board: chess.Board) -> int:
        total = 0
        for color in (chess.WHITE, chess.BLACK):
            ksq = board.king(color)
            if ksq is not None:
                total += len(board.attackers(not color, ksq))
        return total

    def _centre_control(self, board: chess.Board) -> int:
        return sum(
            1 for sq in self._centre
            if board.is_attacked_by(chess.WHITE, sq) or board.is_attacked_by(chess.BLACK, sq)
        )

    @staticmethod
    def _pawn_symmetry(board: chess.Board) -> float:
        """0 = perfect asymmetry, 1 = perfect mirror."""
        sym_pairs = 0
        for file in range(4):  # compare files A/E, B/F, ...
            left_pawns = any(
                board.piece_at(chess.square(file, r)) and
                board.piece_at(chess.square(file, r)).piece_type == chess.PAWN
                for r in range(8)
            )
            right_file = 7 - file
            right_pawns = any(
                board.piece_at(chess.square(right_file, r)) and
                board.piece_at(chess.square(right_file, r)).piece_type == chess.PAWN
                for r in range(8)
            )
            if left_pawns == right_pawns:
                sym_pairs += 1
        return sym_pairs / 4  # 0-1 scale

    # --------------------------------------------------------------- #
    @staticmethod
    def _tactical_danger_zone(board: chess.Board) -> tuple[int, int]:
        """Return (legal_checks, king_attackers)."""
        legal_checks = sum(1 for m in board.legal_moves if board.gives_check(m))
        king_sq = board.king(board.turn)
        attackers = len(board.attackers(not board.turn, king_sq)) if king_sq else 0
        return legal_checks, attackers
