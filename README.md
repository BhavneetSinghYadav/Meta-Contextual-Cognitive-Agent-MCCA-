# Meta-Contextual Cognitive Agent (MCCA)

A modular prototype agent that dynamically switches between multiple internal strategies (tactical, shaping, deception, etc.) based on environmental regime detection.

## Usage
The primary entry point is `build_mcca_agent()` which returns an agent instance. The agent's `act` method **returns two values**: the chosen `chess.Move` and a dictionary of diagnostic information.

```python
import chess
from mcca.agent import build_mcca_agent

board = chess.Board()
agent = build_mcca_agent()

move, diagnostics = agent.act(board)
print("Move:", move)
print("Regime:", diagnostics["final_regime"])
```

The diagnostics object also contains the module blending weights and the detected opponent type. If you previously attempted to unpack four separate values

```python
move, regime, weights, opponent_type = agent.act(board)
```

you will encounter a `ValueError` because only two items are returned. Use the pattern shown above instead.

