import random
import chess

class ShapingModule:
    def __init__(self):
        pass

    def act(self, board: chess.Board):
        """
        Evaluates all legal moves and returns the one that maximizes symbolic entropy:
        - Encourages asymmetry
        - Increases board tension
        - Avoids clean, symmetric, predictable lines
        """
        moves = list(board.legal_moves)
        if not moves:
            return None

        scored = []
        for move in moves:
            board.push(move)
            score = self._entropy_heuristic(board)
            board.pop()
            scored.append((score, move))

        best_move = max(scored, key=lambda x: x[0])[1]
        return best_move

    def _entropy_heuristic(self, board: chess.Board):
        """
        Proxy for symbolic entropy after a move:
        - High mobility (freedom)
        - King separation (destabilization)
        - Center pressure (unsettling balance)
        - Low pawn symmetry (avoids gridlock)
        """
        mobility = len(list(board.legal_moves))

        king_distance = 0
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        if white_king is not None and black_king is not None:
            file_dist = abs(white_king % 8 - black_king % 8)
            rank_dist = abs(white_king // 8 - black_king // 8)
            king_distance = file_dist + rank_dist

        center_pressure = sum(
            1 for sq in [chess.D4, chess.D5, chess.E4, chess.E5]
            if board.is_attacked_by(chess.WHITE, sq) or board.is_attacked_by(chess.BLACK, sq)
        )

        pawn_symmetry = 0
        for file in range(8):
            white_pawn = board.piece_at(chess.square(file, 1))
            black_pawn = board.piece_at(chess.square(file, 6))
            if white_pawn and black_pawn and white_pawn.piece_type == chess.PAWN and black_pawn.piece_type == chess.PAWN:
                pawn_symmetry += 1

        # Entropy proxy score
        entropy_score = (
            1.2 * mobility +
            0.8 * king_distance +
            0.6 * center_pressure -
            0.5 * pawn_symmetry
        )

        return entropy_score
