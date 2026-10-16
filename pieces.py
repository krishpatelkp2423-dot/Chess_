"""Chess rules: how each piece moves.

There is no check or checkmate in this game: the king is a normal piece
worth 2 points that can be captured, and the only way to win is to reach
15 points (see Score in board.py).

The board is an 8x8 list of strings. Uppercase letters are White pieces,
lowercase letters are Black pieces and "" is an empty square. Row 0 is
Black's back rank (the top of the screen when White is at the bottom).
"""

KNIGHT_STEPS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
KING_STEPS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
ROOK_DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
BISHOP_DIRECTIONS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
QUEEN_DIRECTIONS = ROOK_DIRECTIONS + BISHOP_DIRECTIONS


def color_of(piece):
    """Return "white" or "black" for a piece letter."""
    return "white" if piece.isupper() else "black"


def other_color(color):
    return "black" if color == "white" else "white"


def get_valid_moves(board, row, col):
    """Return the squares the piece on (row, col) can move to."""
    piece = board[row][col]
    if piece == "":
        return []
    kind = piece.lower()
    is_white = piece.isupper()
    moves = []

    # Pawn
    if kind == "p":
        direction = -1 if is_white else 1
        start_row = 6 if is_white else 1
        r = row + direction
        if 0 <= r < 8:
            if board[r][col] == "":
                moves.append((r, col))
                if row == start_row and board[r + direction][col] == "":
                    moves.append((r + direction, col))
            for c in (col - 1, col + 1):
                if 0 <= c < 8:
                    target = board[r][c]
                    if target != "" and target.isupper() != is_white:
                        moves.append((r, c))

    # Knight and King: one jump/step in each direction
    elif kind == "n" or kind == "k":
        steps = KNIGHT_STEPS if kind == "n" else KING_STEPS
        for dr, dc in steps:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                target = board[r][c]
                if target == "" or target.isupper() != is_white:
                    moves.append((r, c))

    # Rook, Bishop and Queen: slide until something is in the way
    else:
        if kind == "r":
            directions = ROOK_DIRECTIONS
        elif kind == "b":
            directions = BISHOP_DIRECTIONS
        else:
            directions = QUEEN_DIRECTIONS
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                target = board[r][c]
                if target == "":
                    moves.append((r, c))
                else:
                    if target.isupper() != is_white:
                        moves.append((r, c))
                    break
                r += dr
                c += dc

    return moves


def is_promotion(board, move):
    """True if this move takes a pawn to the far side of the board."""
    (r0, c0), (r1, c1) = move
    piece = board[r0][c0]
    return piece.lower() == "p" and (r1 == 0 or r1 == 7)


def apply_move(board, move, promote_to="q"):
    """Return (new_board, captured_piece) without changing `board`.

    A pawn that reaches the far side is promoted to `promote_to`
    (a queen unless told otherwise).
    """
    new_board = [row[:] for row in board]
    (r0, c0), (r1, c1) = move
    piece = new_board[r0][c0]
    captured = new_board[r1][c1]
    new_board[r1][c1] = piece
    new_board[r0][c0] = ""
    if piece.lower() == "p" and (r1 == 0 or r1 == 7):
        new_board[r1][c1] = promote_to.upper() if piece.isupper() else promote_to.lower()
    return new_board, captured


def get_all_moves(board, color):
    """Every move for `color` as a list of ((from_row, from_col), (to_row, to_col))."""
    moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece != "" and color_of(piece) == color:
                for target in get_valid_moves(board, r, c):
                    moves.append(((r, c), target))
    return moves
