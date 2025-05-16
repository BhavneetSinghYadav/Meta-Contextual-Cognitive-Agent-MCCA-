import random
import chess

class PositionalModule:
    def __init__(self):
        pass

    def act(self, board: chess.Board):
        moves = list(board.legal_moves)
        scored = []

        for move in moves:
            board.push(move)
            score = self._positional_heuristic(board)
            board.pop()
            scored.append((score, move))

        best_move = max(scored, key=lambda x: x[0])[1]
        return best_move

    def _positional_heuristic(self, board):
        # Prefer space, central control, development
        score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                bonus = 0
                if piece.piece_type in [chess.BISHOP, chess.KNIGHT]:
                    bonus = 0.1
                if piece.color:
                    score += (square // 8) + bonus
                else:
                    score -= (7 - square // 8) + bonus
        return score
