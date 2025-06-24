import chess
from mcca.agent import build_mcca_agent

board = chess.Board()
agent = build_mcca_agent()

print("Initial Board:")
print(board)

for i in range(20):
    move, diag = agent.act(board)
    print(f"\nMove {i+1}: {move}")
    board.push(move)
    print(board)

# Gracefully close any module that has a `.close()` method
for name, module in agent.modules.items():
    if hasattr(module, "close"):
        module.close()

