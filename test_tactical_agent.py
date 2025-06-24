import chess
from mcca.modules.tactical_module import TacticalModule

# Set up a starting chess board
board = chess.Board()

# Initialize the tactical module (uses Stockfish with no depth limit)
tactical = TacticalModule()

# Show the current board
print("Initial position:")
print(board)

# Get recommended move and diagnostics
move, diag = tactical.act(board)
print("\nTactical Module suggests:", move)
print("Diagnostics:", diag)

# Play the move on the board
board.push(move)
print("\nBoard after move:")
print(board)

# Close the Stockfish engine process
tactical.close()
