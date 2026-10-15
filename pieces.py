"""Chess rules: how pieces move, check, checkmate and stalemate.

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
    """Return the squares the piece on (row, col) can move to.

    These moves follow how each piece moves but ignore whether the move
    would leave the player's own king in check. Use get_legal_moves for the
    moves a player is actually allowed to make.
    """
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


def find_king(board, color):
    king = "K" if color == "white" else "k"
    for r in range(8):
        if king in board[r]:
            return r, board[r].index(king)
    return None


def is_square_attacked(board, row, col, by_color):
    """True if any piece of `by_color` attacks the square (row, col)."""
    by_white = by_color == "white"

    # Pawns attack one square diagonally forward. White pawns move up the
    # board (towards row 0), so a White pawn attacking (row, col) sits on
    # the row below it.
    pawn = "P" if by_white else "p"
    pawn_row = row + 1 if by_white else row - 1
    if 0 <= pawn_row < 8:
        for c in (col - 1, col + 1):
            if 0 <= c < 8 and board[pawn_row][c] == pawn:
                return True

    knight = "N" if by_white else "n"
    for dr, dc in KNIGHT_STEPS:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == knight:
            return True

    king = "K" if by_white else "k"
    for dr, dc in KING_STEPS:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == king:
            return True

    queen = "Q" if by_white else "q"
    for directions, slider in ((ROOK_DIRECTIONS, "R" if by_white else "r"),
                               (BISHOP_DIRECTIONS, "B" if by_white else "b")):
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                target = board[r][c]
                if target != "":
                    if target == slider or target == queen:
                        return True
                    break
                r += dr
                c += dc

    return False


def is_in_check(board, color):
    """True if `color`'s king is attacked."""
    king_square = find_king(board, color)
    if king_square is None:
        return False
    return is_square_attacked(board, king_square[0], king_square[1], other_color(color))


def get_legal_moves(board, row, col):
    """Moves for the piece on (row, col) that don't leave its own king in check."""
    piece = board[row][col]
    if piece == "":
        return []
    color = color_of(piece)
    legal = []
    for target in get_valid_moves(board, row, col):
        new_board, _ = apply_move(board, ((row, col), target))
        if not is_in_check(new_board, color):
            legal.append(target)
    return legal


def get_all_legal_moves(board, color):
    """Every legal move for `color` as a list of ((from_row, from_col), (to_row, to_col))."""
    moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece != "" and color_of(piece) == color:
                for target in get_legal_moves(board, r, c):
                    moves.append(((r, c), target))
    return moves


def has_legal_move(board, color):
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece != "" and color_of(piece) == color and get_legal_moves(board, r, c):
                return True
    return False


def get_game_status(board, color):
    """Status for the player whose turn it is.

    Returns "checkmate", "stalemate", "check" or "playing".
    """
    in_check = is_in_check(board, color)
    if not has_legal_move(board, color):
        return "checkmate" if in_check else "stalemate"
    return "check" if in_check else "playing"
