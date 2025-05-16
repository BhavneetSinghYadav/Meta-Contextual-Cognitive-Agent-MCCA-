import random
import chess

class ShapingModule:
    def __init__(self):
        pass

    def act(self, board: chess.Board):
        # Goal: Induce entropy, imbalance, avoid clean trades or symmetry
        moves = list(board.legal_moves)
        scored = []

        for move in moves:
            board.push(move)
            score = self._entropy_heuristic(board)
            board.pop()
            scored.append((score, move))

        best_move = max(scored, key=lambda x: x[0])[1]
        return best_move

    def _entropy_heuristic(self, board):
        # Encourage asymmetry and piece tension
        pawn_diff = abs(len(board.pieces(chess.PAWN, True)) - len(board.pieces(chess.PAWN, False)))
        mobility = len(list(board.legal_moves))
        king_dist = abs(board.king(True) % 8 - board.king(False) % 8)
        return mobility + king_dist - pawn_diff  # crude entropy proxy
