"""The computer opponent.

The AI looks ahead with minimax + alpha-beta pruning (written in the
"negamax" style, where each side's score is the other side's score flipped).
When it reaches the end of its search it keeps following captures
("quiescence search") so it doesn't stop in the middle of a trade and
think it won a piece it is about to lose.

It searches one move deeper at a time (iterative deepening) until it runs
out of thinking time, and always plays the best move from the deepest
search it finished.

Positions are scored on:
  * material left on the board,
  * the capture score race (first to WIN_SCORE points wins),
  * where pieces stand (piece-square tables: knights like the centre,
    pawns like to advance, the king likes to hide until the endgame).
"""
import time

from pieces import get_valid_moves, apply_move, is_in_check, other_color, get_all_legal_moves
from board import Score, WIN_SCORE

MATE = 100000  # score for winning; bigger than any normal evaluation
MAX_QUIESCENCE_DEPTH = 6

# How much each piece is worth to the AI, in hundredths of a pawn.
MATERIAL = {"p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 0}
# How much one point on the score board is worth to the AI.
POINT_VALUE = 100
# Below this much non-pawn material (both sides together) the king should
# come out and fight instead of hiding.
ENDGAME_MATERIAL = 2600

# Piece-square tables, from White's side of the board. Row 0 is the far
# side (Black's back rank), so White pieces use table[row][col] and Black
# pieces use the mirrored table[7 - row][col].
PST = {
    "p": [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5, 5, 10, 25, 25, 10, 5, 5],
        [0, 0, 0, 20, 20, 0, 0, 0],
        [5, -5, -10, 0, 0, -10, -5, 5],
        [5, 10, 10, -20, -20, 10, 10, 5],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ],
    "n": [
        [-50, -40, -30, -30, -30, -30, -40, -50],
        [-40, -20, 0, 0, 0, 0, -20, -40],
        [-30, 0, 10, 15, 15, 10, 0, -30],
        [-30, 5, 15, 20, 20, 15, 5, -30],
        [-30, 0, 15, 20, 20, 15, 0, -30],
        [-30, 5, 10, 15, 15, 10, 5, -30],
        [-40, -20, 0, 5, 5, 0, -20, -40],
        [-50, -40, -30, -30, -30, -30, -40, -50],
    ],
    "b": [
        [-20, -10, -10, -10, -10, -10, -10, -20],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-10, 0, 5, 10, 10, 5, 0, -10],
        [-10, 5, 5, 10, 10, 5, 5, -10],
        [-10, 0, 10, 10, 10, 10, 0, -10],
        [-10, 10, 10, 10, 10, 10, 10, -10],
        [-10, 5, 0, 0, 0, 0, 5, -10],
        [-20, -10, -10, -10, -10, -10, -10, -20],
    ],
    "r": [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [5, 10, 10, 10, 10, 10, 10, 5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [0, 0, 0, 5, 5, 0, 0, 0],
    ],
    "q": [
        [-20, -10, -10, -5, -5, -10, -10, -20],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-10, 0, 5, 5, 5, 5, 0, -10],
        [-5, 0, 5, 5, 5, 5, 0, -5],
        [0, 0, 5, 5, 5, 5, 0, -5],
        [-10, 5, 5, 5, 5, 5, 0, -10],
        [-10, 0, 5, 0, 0, 0, 0, -10],
        [-20, -10, -10, -5, -5, -10, -10, -20],
    ],
}
KING_MIDDLEGAME = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [20, 30, 10, 0, 0, 10, 30, 20],
]
KING_ENDGAME = [
    [-50, -40, -30, -20, -20, -30, -40, -50],
    [-30, -20, -10, 0, 0, -10, -20, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -30, 0, 0, 0, 0, -30, -30],
    [-50, -30, -30, -30, -30, -30, -30, -50],
]


def evaluate(board, white_points, black_points):
    """Score the position from White's point of view (positive = good for White)."""
    total = (white_points - black_points) * POINT_VALUE
    non_pawn_material = 0
    kings = []
    for r in range(8):
        row = board[r]
        for c in range(8):
            piece = row[c]
            if piece == "":
                continue
            kind = piece.lower()
            if kind == "k":
                kings.append((piece, r, c))
                continue
            value = MATERIAL[kind]
            if kind != "p":
                non_pawn_material += value
            if piece.isupper():
                total += value + PST[kind][r][c]
            else:
                total -= value + PST[kind][7 - r][c]

    king_table = KING_ENDGAME if non_pawn_material <= ENDGAME_MATERIAL else KING_MIDDLEGAME
    for piece, r, c in kings:
        if piece.isupper():
            total += king_table[r][c]
        else:
            total -= king_table[7 - r][c]
    return total


def _ordered_moves(board, color, captures_only=False):
    """All moves for `color` (not yet checked for king safety), best-looking first.

    Captures of valuable pieces by cheap pieces come first, then promotions,
    then quiet moves. Good ordering lets alpha-beta skip far more positions.
    Returns a list of (move, captured_piece).
    """
    want_upper = color == "white"
    scored = []
    for r in range(8):
        row = board[r]
        for c in range(8):
            piece = row[c]
            if piece == "" or piece.isupper() != want_upper:
                continue
            attacker = MATERIAL[piece.lower()]
            is_pawn = piece.lower() == "p"
            for tr, tc in get_valid_moves(board, r, c):
                captured = board[tr][tc]
                promotes = is_pawn and (tr == 0 or tr == 7)
                if captured != "":
                    order = 10 * MATERIAL[captured.lower()] - attacker + 10000
                elif promotes:
                    order = 9000
                elif captures_only:
                    continue
                else:
                    order = 0
                scored.append((order, ((r, c), (tr, tc)), captured))
    scored.sort(key=lambda item: -item[0])
    return [(move, captured) for _, move, captured in scored]


def _add_points(color, captured, points):
    """Return the (white, black) score after `color` captures `captured`."""
    white_points, black_points = points
    if captured != "":
        value = Score.PIECE_VALUES.get(captured.lower(), 0)
        if color == "white":
            white_points += value
        else:
            black_points += value
    return white_points, black_points


class _OutOfTime(Exception):
    pass


class _Search:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0

    def tick(self):
        self.nodes += 1
        if self.deadline is not None and self.nodes % 512 == 0 and time.time() > self.deadline:
            raise _OutOfTime()

    def negamax(self, board, color, depth, alpha, beta, ply, points):
        """Best score for `color` (the side to move) searching `depth` moves ahead."""
        if depth <= 0:
            return self.quiesce(board, color, alpha, beta, ply, points, 0)
        self.tick()

        best = -MATE * 2
        found_legal_move = False
        for move, captured in _ordered_moves(board, color):
            new_board, _ = apply_move(board, move)
            if is_in_check(new_board, color):
                continue  # illegal: would leave our own king in check
            found_legal_move = True

            new_points = _add_points(color, captured, points)
            my_points = new_points[0] if color == "white" else new_points[1]
            if my_points >= WIN_SCORE:
                return MATE - ply - 1  # this capture wins the score race right now

            value = -self.negamax(new_board, other_color(color), depth - 1, -beta, -alpha, ply + 1, new_points)
            if value > best:
                best = value
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break  # the opponent will never allow this line

        if not found_legal_move:
            # No legal moves: checkmate if in check, otherwise stalemate (a draw).
            return -(MATE - ply) if is_in_check(board, color) else 0
        return best

    def quiesce(self, board, color, alpha, beta, ply, points, qdepth):
        """Only look at captures, so the evaluation isn't taken mid-trade."""
        self.tick()
        stand_pat = evaluate(board, points[0], points[1])
        if color == "black":
            stand_pat = -stand_pat
        if stand_pat >= beta or qdepth >= MAX_QUIESCENCE_DEPTH:
            return stand_pat
        if stand_pat > alpha:
            alpha = stand_pat

        for move, captured in _ordered_moves(board, color, captures_only=True):
            new_board, _ = apply_move(board, move)
            if is_in_check(new_board, color):
                continue
            new_points = _add_points(color, captured, points)
            my_points = new_points[0] if color == "white" else new_points[1]
            if my_points >= WIN_SCORE:
                return MATE - ply - 1
            value = -self.quiesce(new_board, other_color(color), -beta, -alpha, ply + 1, new_points, qdepth + 1)
            if value >= beta:
                return value
            if value > alpha:
                alpha = value
        return alpha

    def search_root(self, board, color, depth, root_moves, points):
        """Search every root move; returns (best_value, moves sorted best first)."""
        alpha, beta = -MATE * 2, MATE * 2
        results = []
        for move in root_moves:
            new_board, captured = apply_move(board, move)
            new_points = _add_points(color, captured, points)
            my_points = new_points[0] if color == "white" else new_points[1]
            if my_points >= WIN_SCORE:
                value = MATE - 1
            else:
                value = -self.negamax(new_board, other_color(color), depth - 1, -beta, -alpha, 1, new_points)
            results.append((value, move))
            if value > alpha:
                alpha = value
        # Stable sort keeps the earlier (previously best) move first on ties.
        results.sort(key=lambda item: -item[0])
        return results[0][0], [move for _, move in results]


def choose_ai_move(board, color, white_score=0, black_score=0, depth=4, think_time=2.0):
    """Pick a move for `color`. Returns ((from_row, from_col), (to_row, to_col)) or None.

    Searches 1 move ahead, then 2, ... up to `depth`, stopping early when
    `think_time` seconds have passed.
    """
    root_moves = get_all_legal_moves(board, color)
    if not root_moves:
        return None
    if len(root_moves) == 1:
        return root_moves[0]

    # Start with the most promising moves (captures, promotions) first.
    order = {move: i for i, (move, _) in enumerate(_ordered_moves(board, color))}
    root_moves.sort(key=lambda move: order.get(move, len(order)))

    points = (white_score, black_score)
    deadline = time.time() + think_time
    best_move = root_moves[0]
    for current_depth in range(1, depth + 1):
        # Depth 1 always finishes so there is always a sensible move.
        search = _Search(deadline if current_depth > 1 else None)
        try:
            best_value, root_moves = search.search_root(board, color, current_depth, root_moves, points)
        except _OutOfTime:
            break
        best_move = root_moves[0]
        if abs(best_value) >= MATE - 100:
            break  # found a forced win (or every move loses): no need to look deeper
    return best_move


class ReinforcementAgent:
    """Wrapper used by main.py. Picks moves with the search above."""

    def __init__(self, depth=4, think_time=2.0):
        self.depth = depth
        self.think_time = think_time

    def select_move(self, board, color, white_score=None, black_score=None):
        if white_score is None or black_score is None:
            from board import score
            white_score, black_score = score.white, score.black
        return choose_ai_move(board, color, white_score, black_score,
                              depth=self.depth, think_time=self.think_time)
