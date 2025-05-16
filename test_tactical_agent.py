import chess
from mcca.modules.tactical_module import TacticalModule

# Set up a starting chess board
board = chess.Board()

# Initialize the tactical module (uses Stockfish)
tactical = TacticalModule(depth=10)

# Show the current board
print("Initial position:")
print(board)

# Get recommended move
move = tactical.act(board)
print("\nTactical Module suggests:", move)

# Play the move on the board
board.push(move)
print("\nBoard after move:")
print(board)

# Close the Stockfish engine process
tactical.close()
