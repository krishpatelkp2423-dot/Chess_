import random
import copy
from pieces import get_valid_moves
from board import Score


def _piece_value(ch):
    return Score.PIECE_VALUES.get(ch.lower(), 0)


def generate_legal_moves(board, color):
    moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "":
                continue
            if (piece.isupper() and color == "white") or (piece.islower() and color == "black"):
                for tr, tc in get_valid_moves(board, r, c):
                    moves.append(((r, c), (tr, tc)))
    return moves


def material_counts(board):
    white = 0
    black = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p == "":
                continue
            v = _piece_value(p)
            if p.isupper():
                white += v
            else:
                black += v
    return white, black


def evaluate(board, white_score, black_score, ai_color):
    # Evaluate in perspective of ai_color: higher is better for AI
    mat_w, mat_b = material_counts(board)
    total_w = white_score + mat_w
    total_b = black_score + mat_b
    val = total_w - total_b
    if ai_color == "white":
        return val
    return -val


def apply_move(board, move):
    # Return new board copy and captured piece (or "")
    newb = [row[:] for row in board]
    (r0, c0), (r1, c1) = move
    captured = newb[r1][c1]
    newb[r1][c1] = newb[r0][c0]
    newb[r0][c0] = ""
    return newb, captured


def order_moves(board, moves):
    # Simple ordering: captures first (by captured value desc), then others
    scored = []
    for mv in moves:
        (r0, c0), (r1, c1) = mv
        target = board[r1][c1]
        score = _piece_value(target) if target != "" else 0
        scored.append((score, mv))
    scored.sort(key=lambda x: -x[0])
    return [mv for _, mv in scored]


def minimax(board, white_score, black_score, depth, maximizing_color, ai_color, alpha, beta):
    # Returns (best_value, best_move) from perspective of ai_color
    # Terminal: depth==0 or no moves for player
    moves = generate_legal_moves(board, maximizing_color)
    if depth == 0 or not moves:
        return evaluate(board, white_score, black_score, ai_color), None

    best_move = None
    moves = order_moves(board, moves)

    if maximizing_color == ai_color:
        value = -10**9
        for mv in moves:
            newb, captured = apply_move(board, mv)
            w_score = white_score
            b_score = black_score
            if captured != "":
                if captured.isupper():
                    # white piece captured by black move
                    b_score += _piece_value(captured)
                else:
                    w_score += _piece_value(captured)

            nxt_color = "black" if maximizing_color == "white" else "white"
            val, _ = minimax(newb, w_score, b_score, depth - 1, nxt_color, ai_color, alpha, beta)
            if val > value:
                value = val
                best_move = mv
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = 10**9
        for mv in moves:
            newb, captured = apply_move(board, mv)
            w_score = white_score
            b_score = black_score
            if captured != "":
                if captured.isupper():
                    b_score += _piece_value(captured)
                else:
                    w_score += _piece_value(captured)

            nxt_color = "black" if maximizing_color == "white" else "white"
            val, _ = minimax(newb, w_score, b_score, depth - 1, nxt_color, ai_color, alpha, beta)
            if val < value:
                value = val
                best_move = mv
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move


def choose_ai_move(board, color, white_score=0, black_score=0, depth=3):
    # Try minimax first; fallback to greedy/random
    try:
        val, mv = minimax(board, white_score, black_score, depth, color, color, -10**9, 10**9)
        if mv is not None:
            return mv
    except Exception:
        pass

    # fallback: greedy as before
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
        maxv = max(c[2] for c in captures)
        best = [c for c in captures if c[2] == maxv]
        pick = random.choice(best)
        return (pick[0], pick[1])

    if moves:
        return random.choice(moves)

    return None


class ReinforcementAgent:
    """Agent wrapper: for now select_move uses minimax search to choose moves."""
    def __init__(self, depth=3):
        self.depth = depth

    def select_move(self, board, color):
        # compute current scores from global score object if available
        try:
            from board import score
            ws = score.white
            bs = score.black
        except Exception:
            ws, bs = 0, 0
        return choose_ai_move(board, color, white_score=ws, black_score=bs, depth=self.depth)
