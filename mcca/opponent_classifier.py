# File: mcca/opponent_classifier.py
"""
OpponentClassifier v3.2
-----------------------
Symbolic play-style profiler for the Meta-Contextual Cognitive Agent.

API
---
update(board_before, move)   -> None
classify()                   -> dict   (profile object, see below)

Returned profile:
{
  "type": "tactical" | "positional" | "shaping" | "deception" | "chaotic" | "unknown",
  "confidence": float,          # 0-1
  "scores": {style: float, ...},
  "reason": str,                # short human-readable justification
  "volatile": bool              # high oscillation flag
}
"""

from __future__ import annotations
import chess
from typing import Dict, Any, List, Tuple


class OpponentClassifier:
    # --------------------------------------------------------------- #
    def __init__(self):
        self.history: List[Tuple[chess.Board, chess.Move]] = []
        self.window = 12   # sliding window length

    # --------------------------------------------------------------- #
    def update(self, board: chess.Board, move: chess.Move):
        self.history.append((board.copy(), move))
        if len(self.history) > self.window:
            self.history.pop(0)

    # --------------------------------------------------------------- #
    def classify(self) -> Dict[str, Any]:
        if len(self.history) < 6:
            return {"type": "unknown", "confidence": 0.0,
                    "scores": {}, "reason": "insufficient data", "volatile": False}

        states = [s for s, _ in self.history[-self.window:]]
        moves = [m for _, m in self.history[-self.window:]]

        tac = self._tactical_aggr(states, moves)
        shp = self._entropy_induction(states, moves)
        pos = self._quiet_reposition(states, moves)
        dec = self._deception_signal(states, moves)
        vol = self._volatility_score([tac, pos, shp, dec])

        scores = {"tactical": tac, "positional": pos,
                  "shaping": shp, "deception": dec}

        # primary classification
        top_style, top_val = max(scores.items(), key=lambda kv: kv[1])
        sorted_vals = sorted(scores.values(), reverse=True)
        next_best = sorted_vals[1]

        # chaotic label
        chaotic = (shp >= 4 and tac >= 4) or vol
        style = "chaotic" if chaotic else top_style

        # confidence estimation
        conf = 0.5
        if top_val >= 4 and top_val >= 1.8 * next_best:
            conf = 0.85
        elif top_val >= 3:
            conf = 0.7
        elif chaotic:
            conf = 0.6

        reason = self._build_reason(style, scores, chaotic, vol)

        return {
            "type": style,
            "confidence": round(conf, 2),
            "scores": {k: round(v, 2) for k, v in scores.items()},
            "reason": reason,
            "volatile": vol
        }

    # --------------------------------------------------------------- #
    # INDIVIDUAL STYLE METRICS
    # --------------------------------------------------------------- #
    def _tactical_aggr(self, states, moves) -> float:
        score = 0.0
        for s, m in zip(states, moves):
            if s.is_capture(m):
                score += 1.5
            if s.gives_check(m):
                score += 1.2
            if m.promotion:
                score += 1.0
        return score

    def _entropy_induction(self, states, moves) -> float:
        score = 0.0
        for s, m in zip(states, moves):
            # flank pawn storms or rook lifts
            if chess.square_file(m.from_square) in (0, 7):
                score += 0.8
            # en-passant attempts
            if s.is_en_passant(m):
                score += 1.0
            # wide pawn shifts
            piece = s.piece_at(m.from_square)
            if piece and piece.piece_type == chess.PAWN:
                lateral = abs(chess.square_file(m.to_square) -
                              chess.square_file(m.from_square))
                if lateral >= 2:
                    score += 0.6
        return score

    def _quiet_reposition(self, states, moves) -> float:
        score = 0.0
        for s, m in zip(states, moves):
            piece = s.piece_at(m.from_square)
            if piece and piece.piece_type in (chess.KNIGHT, chess.BISHOP, chess.ROOK):
                if not s.is_capture(m) and not s.gives_check(m):
                    # prefer re-centralising moves
                    rank_from = m.from_square // 8
                    rank_to = m.to_square // 8
                    if piece.color == chess.WHITE and rank_to > rank_from:
                        score += 1.0
                    elif piece.color == chess.BLACK and rank_to < rank_from:
                        score += 1.0
        return score

    def _deception_signal(self, states, moves) -> float:
        """Crude bait / bluff score: undefended mobility & retreats."""
        score = 0.0
        for s, m in zip(states, moves):
            piece = s.piece_at(m.from_square)
            if not piece:
                continue
            # apparent retreat
            retreat = (m.to_square // 8 <
                       m.from_square // 8) if piece.color == chess.WHITE else \
                      (m.to_square // 8 > m.from_square // 8)
            if retreat:
                score += 0.6

            # leaves piece hanging
            s.push(m)
            attackers = s.attackers(not piece.color, m.to_square)
            defenders = s.attackers(piece.color, m.to_square)
            if attackers and not defenders:
                score += 1.0
            s.pop()
        return score

    # --------------------------------------------------------------- #
    def _volatility_score(self, vals: list[float]) -> bool:
        # high oscillation among style scores (std dev)
        mean = sum(vals) / 4
        variance = sum((v - mean) ** 2 for v in vals) / 4
        return variance >= 4.0  # threshold tuned empirically

    # --------------------------------------------------------------- #
    @staticmethod
    def _build_reason(style, scores, chaotic, vol) -> str:
        parts: List[str] = []
        if chaotic:
            parts.append("chaotic mix")
        elif vol:
            parts.append("volatile pattern")
        top = max(scores.items(), key=lambda kv: kv[1])
        parts.append(f"top={top[0]}({round(top[1],1)})")
        return ", ".join(parts)
