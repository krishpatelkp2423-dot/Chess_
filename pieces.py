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


def handle_click(board, pos, selected, turn, SQUARE_SIZE, score=None, flipped=False, screen=None):
    # map screen position to board coordinates depending on view flip
    if not flipped:
        col = pos[0] // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE
    else:
        col = 7 - (pos[0] // SQUARE_SIZE)
        row = 7 - (pos[1] // SQUARE_SIZE)
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
            # Score.add now returns the winner (or None) when threshold reached
            winner = score.add(turn, captured)
            if winner is not None:
                # debug output to terminal for visibility
                print(f"DEBUG: {turn} captured {captured!r} -> scores white={score.white} black={score.black} winner={winner}")

        # perform the move
        board[row][col] = board[selected[0]][selected[1]]
        board[selected[0]][selected[1]] = ""

        # promotion: if a pawn reached the far rank, prompt for piece choice
        moved = board[row][col]
        if moved.lower() == "p" and screen is not None:
            # white pawns promote when reaching row 0; black pawns when row 7
            if (moved.isupper() and row == 0) or (moved.islower() and row == 7):
                try:
                    from promotion import prompt_promotion
                    color = "white" if moved.isupper() else "black"
                    choice = prompt_promotion(screen, color)
                    if choice:
                        board[row][col] = choice
                except Exception as e:
                    # if promotion UI fails, leave pawn as-is and print error
                    print("Promotion error:", e)

        next_turn = "black" if turn == "white" else "white"
        return None, [], next_turn, winner

    elif piece != "" and (piece.isupper() == (turn == "white")):
        return (row, col), [], turn, None

    return None, [], turn, None