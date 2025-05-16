import random
import chess

class PositionalModule:
    def __init__(self):
        self.center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
        self.strong_center = [chess.C4, chess.F4, chess.C5, chess.F5]

    def act(self, board: chess.Board):
        moves = list(board.legal_moves)
        if not moves:
            return None

        scored = []
        for move in moves:
            board.push(move)
            score = self._positional_heuristic(board)
            board.pop()
            scored.append((score, move))

        best_move = max(scored, key=lambda x: x[0])[1]
        return best_move

    def _positional_heuristic(self, board: chess.Board):
        score = 0

        # Central control
        center_pressure = sum(
            1 for square in self.center_squares
            if board.is_attacked_by(chess.WHITE, square)
        )
        extended_center_pressure = sum(
            0.5 for square in self.strong_center
            if board.is_attacked_by(chess.WHITE, square)
        )
        score += 1.2 * center_pressure + extended_center_pressure

        # Minor piece development
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == chess.WHITE:
                rank = square // 8
                file = square % 8
                if piece.piece_type == chess.KNIGHT:
                    if rank >= 2:
                        score += 0.4
                elif piece.piece_type == chess.BISHOP:
                    if rank >= 2:
                        score += 0.3
                elif piece.piece_type == chess.ROOK:
                    if file in [3, 4]:  # central files
                        score += 0.3
                elif piece.piece_type == chess.QUEEN:
                    if rank >= 2:
                        score += 0.2
                elif piece.piece_type == chess.KING:
                    if square in [chess.G1, chess.C1]:
                        score += 0.5  # castled
                    elif rank in [2, 3, 4]:
                        score -= 0.7  # king in the center

        # Pawn structure (penalize isolated or doubled pawns)
        pawn_files = [square % 8 for square in board.pieces(chess.PAWN, chess.WHITE)]
        file_counts = {f: pawn_files.count(f) for f in range(8)}
        for f in file_counts:
            if file_counts[f] >= 2:
                score -= 0.3  # doubled pawn penalty
            if file_counts[f] == 1:
                if f == 0 or f == 7 or file_counts.get(f - 1, 0) == 0 and file_counts.get(f + 1, 0) == 0:
                    score -= 0.4  # isolated pawn

        return round(score, 3)
