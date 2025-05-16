import random
import chess

class DeceptionModule:
    def __init__(self):
        pass

    def act(self, board: chess.Board):
        """
        Selects a move that maximizes symbolic deception:
        - Creates phantom threats
        - Baits opponent into bad responses
        - Withdraws pieces deceptively
        - Leaves hanging pieces with indirect defense
        """
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        scored = []
        for move in legal_moves:
            board.push(move)
            score = self._deception_heuristic(board, move)
            board.pop()
            scored.append((score, move))

        best_move = max(scored, key=lambda x: x[0])[1]
        return best_move

    def _deception_heuristic(self, board: chess.Board, move: chess.Move):
        """
        Heuristic: score moves that:
        - Create illusory threats
        - Leave apparent bait (undefended or hanging pieces)
        - Withdraw active pieces to create pressure retraction
        - Manipulate opponent king safety or piece alignment
        """
        score = 0

        opponent_color = not board.turn

        # 1. Phantom pressure: squares attacked without being fully committed
        phantom_threats = 0
        for square in chess.SQUARES:
            if board.is_attacked_by(board.turn, square) and not board.is_attacked_by(opponent_color, square):
                phantom_threats += 1
        score += 0.5 * phantom_threats

        # 2. Bait exposure: friendly piece that becomes "apparently" capturable
        hanging_bait = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == board.turn:
                attackers = board.attackers(opponent_color, square)
                defenders = board.attackers(board.turn, square)
                if attackers and not defenders:
                    hanging_bait += 1
        score += 0.7 * hanging_bait

        # 3. Retreat from confrontation (illusion of weakness)
        if move.from_square in board.attacks(move.to_square):
            score += 0.5  # move appears passive

        # 4. Manipulate king distance
        my_king = board.king(board.turn)
        opp_king = board.king(opponent_color)
        if my_king and opp_king:
            file_diff = abs(my_king % 8 - opp_king % 8)
            rank_diff = abs(my_king // 8 - opp_king // 8)
            distance = file_diff + rank_diff
            if distance >= 5:
                score += 0.3  # create board disconnection

        # 5. Random noise to prevent determinism
        score += random.uniform(0, 0.3)

        return round(score, 3)
