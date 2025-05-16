import random
import chess

class DeceptionModule:
    def __init__(self):
        pass

    def act(self, board: chess.Board):
        # Prefer bait, threat illusion, retractions, strange delays
        moves = list(board.legal_moves)
        random.shuffle(moves)
        scored = []

        for move in moves:
            board.push(move)
            threat = self._phantom_threat_score(board)
            board.pop()
            scored.append((threat, move))

        best_move = max(scored, key=lambda x: x[0])[1]
        return best_move

    def _phantom_threat_score(self, board):
        attackers = sum(len(board.attackers(not board.turn, sq)) for sq in chess.SQUARES)
        return -attackers + random.random() * 0.5
