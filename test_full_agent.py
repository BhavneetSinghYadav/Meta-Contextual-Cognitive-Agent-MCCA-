# File: test_full_agent.py

import chess
from mcca.agent import build_mcca_agent

# Initialize board and agent
board = chess.Board()
agent = build_mcca_agent()

print("Initial Board:")
print(board)

# Play 5 moves using the MCCA agent
for i in range(5):
    move = agent.act(board)
    print(f"\nMove {i+1}: {move}")
    board.push(move)
    print(board)
tactical.close()
