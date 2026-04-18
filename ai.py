import random
from pieces import get_valid_moves
from board import Score


def _piece_value(ch):
    return Score.PIECE_VALUES.get(ch.lower(), 0)


def choose_ai_move(board, color):
    """Return a move for the AI as ((r_from,c_from),(r_to,c_to)).

    Strategy (simple): prefer captures with highest value; otherwise pick a
    random legal move. This is a placeholder for a reinforcement/ML agent.
    """
    moves = []
    captures = []

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "":
                continue
            if (piece.isupper() and color == "white") or (piece.islower() and color == "black"):
                valid = get_valid_moves(board, r, c)
                for (tr, tc) in valid:
                    target = board[tr][tc]
                    if target != "":
                        captures.append(((r, c), (tr, tc), _piece_value(target)))
                    else:
                        moves.append(((r, c), (tr, tc)))

    if captures:
        # choose capture with max value, break ties randomly
        maxv = max(c[2] for c in captures)
        best = [c for c in captures if c[2] == maxv]
        pick = random.choice(best)
        return (pick[0], pick[1])

    if moves:
        return random.choice(moves)

    return None


class ReinforcementAgent:
    """Placeholder class showing where a reinforcement model could live.

    To implement: maintain a policy network that maps board states to move
    probabilities, use self-play or environment rollouts to update.
    """
    def __init__(self):
        # placeholder storage for learned parameters
        self.policy = None

    def select_move(self, board, color):
        # for now delegate to choose_ai_move
        return choose_ai_move(board, color)
