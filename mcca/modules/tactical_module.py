import random
import chess
import chess.engine

class TacticalModule:
    def __init__(self, stockfish_path="/usr/games/stockfish", depth=10):
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        self.depth = depth

    def act(self, board: chess.Board):
        result = self.engine.analyse(board, chess.engine.Limit(depth=self.depth))
        best_move = result.get("pv", [None])[0]
        if best_move is None:
            return random.choice(list(board.legal_moves))
        return best_move

    def close(self):
        self.engine.quit()
