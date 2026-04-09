def get_valid_moves(board, row, col):
    piece = board[row][col].lower()
    is_white = board[row][col].isupper()
    moves = []

    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def is_enemy(r, c):
        if board[r][c] == "":
            return False
        return board[r][c].isupper() != is_white

    def is_empty(r, c):
        return board[r][c] == ""

    def slide(directions):
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while in_bounds(r, c):
                if is_empty(r, c):
                    moves.append((r, c))
                elif is_enemy(r, c):
                    moves.append((r, c))
                    break
                else:
                    break
                r += dr
                c += dc

    # Pawn
    if piece == "p":
        direction = -1 if is_white else 1
        start_row = 6 if is_white else 1
        r = row + direction
        if in_bounds(r, col) and is_empty(r, col):
            moves.append((r, col))
            if row == start_row and is_empty(row + 2 * direction, col):
                moves.append((row + 2 * direction, col))
        for dc in [-1, 1]:
            if in_bounds(r, col + dc) and is_enemy(r, col + dc):
                moves.append((r, col + dc))

    # Rook
    elif piece == "r":
        slide([(1,0),(-1,0),(0,1),(0,-1)])

    # Bishop
    elif piece == "b":
        slide([(1,1),(1,-1),(-1,1),(-1,-1)])

    # Queen
    elif piece == "q":
        slide([(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)])

    # Knight
    elif piece == "n":
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            r, c = row + dr, col + dc
            if in_bounds(r, c) and (is_empty(r, c) or is_enemy(r, c)):
                moves.append((r, c))

    # King
    elif piece == "k":
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if in_bounds(r, c) and (is_empty(r, c) or is_enemy(r, c)):
                    moves.append((r, c))

    return moves


def handle_click(board, pos, selected, turn, SQUARE_SIZE, score=None):
    col = pos[0] // SQUARE_SIZE
    row = pos[1] // SQUARE_SIZE
    piece = board[row][col]

    if selected is None:
        if piece != "" and (piece.isupper() == (turn == "white")):
            return (row, col), [], turn, None
        return None, [], turn, None

    valid_moves = get_valid_moves(board, selected[0], selected[1])

    if (row, col) in valid_moves:
        # capture handling: if target square has an enemy piece, update score
        captured = board[row][col]
        winner = None
        if captured != "" and score is not None:
            # the mover is 'turn'
            score.add(turn, captured)
            # check for end condition: first to reach 15 points wins
            if score.white >= 15:
                winner = "white"
            elif score.black >= 15:
                winner = "black"

        board[row][col] = board[selected[0]][selected[1]]
        board[selected[0]][selected[1]] = ""
        next_turn = "black" if turn == "white" else "white"
        return None, [], next_turn, winner

    elif piece != "" and (piece.isupper() == (turn == "white")):
        return (row, col), [], turn, None
    return None, [], turn, None