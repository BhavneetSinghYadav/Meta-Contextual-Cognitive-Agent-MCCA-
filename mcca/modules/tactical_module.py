import random
import chess
import chess.engine

class TacticalModule:
    def __init__(self, stockfish_path="/usr/games/stockfish", depth=10):
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        self.depth = depth

    def act(self, board: chess.Board):
        """
        Returns the best move from Stockfish analysis, along with its evaluation.
        Falls back to a random legal move if evaluation fails.
        """
        try:
            result = self.engine.analyse(board, chess.engine.Limit(depth=self.depth))
            best_move = result.get("pv", [None])[0]
            score = result.get("score", None)
            if best_move is None:
                fallback = random.choice(list(board.legal_moves))
                return fallback, None
            return best_move, score
        except Exception as e:
            print(f"[TacticalModule] Engine failure: {e}")
            fallback = random.choice(list(board.legal_moves))
            return fallback, None

    def evaluate(self, board: chess.Board):
        """
        Returns evaluation score only, without suggesting a move.
        Useful for eval drift detection or regime-aware introspection.
        """
        try:
            result = self.engine.analyse(board, chess.engine.Limit(depth=self.depth))
            return result.get("score", None)
        except Exception as e:
            print(f"[TacticalModule] Evaluation failed: {e}")
            return None

    def close(self):
        self.engine.quit()
