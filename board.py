import os

import pygame

# Settings
# Keep the board area square and add a right-hand sidebar for score/ui
BOARD_WIDTH = 800
SIDEBAR_WIDTH = 200
WIDTH, HEIGHT = BOARD_WIDTH + SIDEBAR_WIDTH, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = BOARD_WIDTH // COLS
WIN_SCORE = 15  # first player to capture this many points wins

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
SIDEBAR_BG = (230, 230, 230)
TEXT = (30, 30, 30)
MUTED_TEXT = (100, 100, 100)
CHECK_RED = (220, 40, 40)
# Highlights are drawn see-through (the 4th number is the transparency)
SELECTED_TINT = (60, 170, 60, 150)
LAST_MOVE_TINT = (255, 225, 50, 110)
MOVE_DOT = (30, 30, 30, 90)

# The font that ships with the game. DejaVu Sans includes the chess
# symbols, so the pieces look the same on every computer.
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DejaVuSans-Bold.ttf")

# Unicode chess symbols. The "solid" set is drawn for the body of the piece
# and the "outline" set on top of White pieces for their black edges.
SOLID_SYMBOLS = {"k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"}
OUTLINE_SYMBOLS = {"k": "♔", "q": "♕", "r": "♖", "b": "♗", "n": "♘", "p": "♙"}
PIECE_NAMES = {"k": "King", "q": "Queen", "r": "Rook", "b": "Bishop", "n": "Knight", "p": "Pawn"}

# Board layout
START_POSITION = [
    ["r", "n", "b", "q", "k", "b", "n", "r"],
    ["p", "p", "p", "p", "p", "p", "p", "p"],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["P", "P", "P", "P", "P", "P", "P", "P"],
    ["R", "N", "B", "Q", "K", "B", "N", "R"],
]
board = [row[:] for row in START_POSITION]


def reset_board():
    """Put every piece back on its starting square (keeps the same list object)."""
    board[:] = [row[:] for row in START_POSITION]


# Piece values for scoring
class Score:
    # Kings can't be captured (you must get out of check), so they have no value.
    PIECE_VALUES = {
        "p": 1,
        "n": 3,
        "b": 3,
        "r": 5,
        "q": 9,
    }

    def __init__(self):
        self.white = 0
        self.black = 0

    def reset(self):
        self.white = 0
        self.black = 0

    def add(self, capturing_color, piece_char):
        """Add the value of piece_char to capturing_color ('white' or 'black').

        Returns the winning color once someone reaches WIN_SCORE, else None.
        """
        if not piece_char:
            return None
        value = self.PIECE_VALUES.get(piece_char.lower(), 0)
        if capturing_color == "white":
            self.white += value
        else:
            self.black += value

        if self.white >= WIN_SCORE:
            return "white"
        if self.black >= WIN_SCORE:
            return "black"
        return None


score = Score()


# ---------------------------------------------------------------------------
# Fonts and piece pictures (made once, then reused every frame)
# ---------------------------------------------------------------------------
_fonts = {}
_piece_fonts = {}
_piece_images = {}
# Offsets used to draw the light halo around Black pieces
HALO_OFFSETS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]


def get_font(size):
    """The bundled DejaVu font at `size`, falling back to pygame's default font."""
    if size not in _fonts:
        try:
            _fonts[size] = pygame.font.Font(FONT_PATH, size)
        except (OSError, pygame.error):
            _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def _has_chess_symbols(font):
    """True if `font` really draws the chess symbols.

    A font without them draws the same empty box for every symbol, so the
    king and the queen would come out exactly the same.
    """
    try:
        if any(m is None for m in font.metrics(SOLID_SYMBOLS["k"] + SOLID_SYMBOLS["q"])):
            return False
        king = pygame.mask.from_surface(font.render(SOLID_SYMBOLS["k"], True, BLACK))
        queen = pygame.mask.from_surface(font.render(SOLID_SYMBOLS["q"], True, BLACK))
    except pygame.error:
        return False
    same = king.get_size() == queen.get_size() and king.count() == queen.count() == king.overlap_area(queen, (0, 0))
    return king.count() > 0 and not same


def get_piece_font(size):
    """A font that can draw the chess symbols, or None if none can be found.

    Uses the bundled font, or if that is missing, a system font that has them.
    """
    if size not in _piece_fonts:
        _piece_fonts[size] = None
        font = get_font(size)
        if _has_chess_symbols(font):
            _piece_fonts[size] = font
        else:
            for name in ("dejavusans", "freeserif", "symbola", "notosanssymbols2",
                         "applesymbols", "segoeuisymbol", "arialunicodems"):
                path = pygame.font.match_font(name)
                if not path:
                    continue
                try:
                    font = pygame.font.Font(path, size)
                except (OSError, pygame.error):
                    continue
                if _has_chess_symbols(font):
                    _piece_fonts[size] = font
                    break
    return _piece_fonts[size]


def _holes_mask(glyph):
    """Mask of the gaps inside a glyph (e.g. the cross cut out of a bishop),
    so they can be painted in instead of showing the square underneath."""
    w, h = glyph.get_size()
    padded = pygame.mask.Mask((w + 2, h + 2))
    padded.draw(pygame.mask.from_surface(glyph), (1, 1))
    padded.invert()
    padded.erase(padded.connected_component((0, 0)), (0, 0))  # remove the outside
    holes = pygame.mask.Mask((w, h))
    holes.draw(padded, (-1, -1))
    return holes


def _render_symbol_piece(piece, size, font):
    kind = piece.lower()
    solid, outline = SOLID_SYMBOLS[kind], OUTLINE_SYMBOLS[kind]
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    glyph = font.render(solid, True, BLACK)
    rect = glyph.get_rect(center=(size // 2, size // 2 + size // 50))
    holes = _holes_mask(glyph)

    def paint_body(color, dx=0, dy=0):
        layer = font.render(solid, True, color)
        image.blit(layer, rect.move(dx, dy))
        image.blit(holes.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0)), rect.move(dx, dy))

    # soft drop shadow
    shadow = pygame.Surface((size, size), pygame.SRCALPHA)
    shadow.blit(font.render(solid, True, BLACK), rect.move(size // 50, size // 33))
    shadow.set_alpha(60)
    image.blit(shadow, (0, 0))

    if piece.isupper():
        # White piece: white body with black outline and details
        paint_body((250, 250, 250))
        image.blit(font.render(outline, True, (20, 20, 20)), rect)
    else:
        # Black piece: light halo so it stands out on dark squares, then a
        # dark body whose cut-out details show the light colour underneath
        halo = (235, 235, 235)
        for dx, dy in HALO_OFFSETS:
            paint_body(halo, dx * 2, dy * 2)
        paint_body(halo)
        image.blit(font.render(solid, True, (30, 30, 30)), rect)
    return image


def _render_letter_piece(piece, size):
    """Backup look (a circle with a letter) if the chess symbols can't be drawn."""
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (size // 2, size // 2)
    radius = max(8, size // 2 - 8)
    if piece.isupper():
        fill, outline, text_color = WHITE, (50, 50, 50), (20, 20, 20)
    else:
        fill, outline, text_color = (30, 30, 30), (200, 200, 200), WHITE
    pygame.draw.circle(image, fill, center, radius)
    pygame.draw.circle(image, outline, center, radius, 2)
    text = get_font(size // 2).render(piece.upper(), True, text_color)
    image.blit(text, text.get_rect(center=center))
    return image


def get_piece_image(piece, size=SQUARE_SIZE):
    """Picture of `piece` ("K", "q", ...) as a size x size transparent surface."""
    key = (piece, size)
    if key not in _piece_images:
        font = get_piece_font(int(size * 0.78))
        if font is not None:
            _piece_images[key] = _render_symbol_piece(piece, size, font)
        else:
            _piece_images[key] = _render_letter_piece(piece, size)
    return _piece_images[key]


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
def board_to_screen(row, col, flipped):
    """Top-left pixel of a board square. When flipped, Black is at the bottom."""
    if flipped:
        row, col = 7 - row, 7 - col
    return col * SQUARE_SIZE, row * SQUARE_SIZE


def screen_to_board(x, y, flipped):
    """Board (row, col) under a pixel, or None if it's outside the board."""
    if not (0 <= x < BOARD_WIDTH and 0 <= y < BOARD_WIDTH):
        return None
    row, col = y // SQUARE_SIZE, x // SQUARE_SIZE
    if flipped:
        row, col = 7 - row, 7 - col
    return row, col


def _tint_square(screen, row, col, color, flipped):
    tint = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    tint.fill(color)
    screen.blit(tint, board_to_screen(row, col, flipped))


def draw_board(screen, board, selected=None, valid_moves=(), flipped=False, last_move=None, check_square=None):
    """Draw the squares, coordinates and highlights.

    selected, valid_moves, last_move and check_square are in board
    coordinates and are mapped to the screen when flipped.
    """
    label_font = get_font(14)
    files = "abcdefgh"

    for row in range(ROWS):
        for col in range(COLS):
            color = LIGHT if (row + col) % 2 == 0 else DARK
            x, y = board_to_screen(row, col, flipped)
            pygame.draw.rect(screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

            # coordinates along the left and bottom edges of the screen
            other = DARK if color == LIGHT else LIGHT
            if x == 0:
                label = label_font.render(str(8 - row), True, other)
                screen.blit(label, (x + 4, y + 3))
            if y == SQUARE_SIZE * 7:
                label = label_font.render(files[col], True, other)
                screen.blit(label, (x + SQUARE_SIZE - label.get_width() - 4, y + SQUARE_SIZE - label.get_height() - 2))

    if last_move is not None:
        for row, col in last_move:
            _tint_square(screen, row, col, LAST_MOVE_TINT, flipped)

    if selected is not None:
        _tint_square(screen, selected[0], selected[1], SELECTED_TINT, flipped)

    if check_square is not None:
        x, y = board_to_screen(check_square[0], check_square[1], flipped)
        glow = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        center = (SQUARE_SIZE // 2, SQUARE_SIZE // 2)
        for i in range(10, 0, -1):
            pygame.draw.circle(glow, CHECK_RED + (int(230 * (1 - i / 10)) + 25,), center, SQUARE_SIZE * i // 15)
        screen.blit(glow, (x, y))

    # move indicators: a dot on empty squares, a ring around capturable pieces
    marker = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    for r, c in valid_moves:
        marker.fill((0, 0, 0, 0))
        center = (SQUARE_SIZE // 2, SQUARE_SIZE // 2)
        if board[r][c] == "":
            pygame.draw.circle(marker, MOVE_DOT, center, SQUARE_SIZE // 7)
        else:
            pygame.draw.circle(marker, MOVE_DOT, center, SQUARE_SIZE // 2 - 2, SQUARE_SIZE // 12)
        screen.blit(marker, board_to_screen(r, c, flipped))


def draw_pieces(screen, board, flipped=False):
    """Draw every piece using its chess symbol."""
    for row in range(ROWS):
        for col in range(COLS):
            piece = board[row][col]
            if piece != "":
                screen.blit(get_piece_image(piece), board_to_screen(row, col, flipped))


def draw_sidebar(screen, score, turn, status="", ai_color=None):
    """Score, whose turn it is, game messages and piece values on the right."""
    pygame.draw.rect(screen, SIDEBAR_BG, (BOARD_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT))
    pygame.draw.line(screen, (190, 190, 190), (BOARD_WIDTH, 0), (BOARD_WIDTH, HEIGHT), 2)

    title_font = get_font(26)
    font = get_font(18)
    small = get_font(14)
    x = BOARD_WIDTH + 20
    y = 20

    screen.blit(title_font.render("Score", True, TEXT), (x, y))
    y += 42
    for color, points in (("white", score.white), ("black", score.black)):
        screen.blit(get_piece_image("K" if color == "white" else "k", 30), (x - 4, y - 4))
        label = color.capitalize()
        if ai_color == color:
            label += " (AI)"
        screen.blit(font.render(f"{label}: {points}", True, TEXT), (x + 30, y))
        y += 32
    screen.blit(small.render(f"(first to {WIN_SCORE} wins)", True, MUTED_TEXT), (x, y))
    y += 36

    # whose turn
    pygame.draw.rect(screen, WHITE if turn == "white" else (40, 40, 40), (x, y, 160, 34), border_radius=6)
    pygame.draw.rect(screen, (120, 120, 120), (x, y, 160, 34), 1, border_radius=6)
    turn_text = font.render(f"{turn.capitalize()} to move", True, TEXT if turn == "white" else WHITE)
    screen.blit(turn_text, turn_text.get_rect(center=(x + 80, y + 17)))
    y += 46

    for line in status.split("\n") if status else []:
        color = CHECK_RED if line.lower().startswith("check") else TEXT
        screen.blit(font.render(line, True, color), (x, y))
        y += 26
    y = max(y, 330)

    # piece values legend, using the piece symbols
    screen.blit(font.render("Values:", True, TEXT), (x, y))
    y += 28
    for p, v in Score.PIECE_VALUES.items():
        screen.blit(get_piece_image(p.upper(), 30), (x - 4, y - 5))
        screen.blit(font.render(f"{PIECE_NAMES[p]}: {v}", True, TEXT), (x + 30, y))
        y += 30

    # controls
    y = HEIGHT - 70
    for line in ("R  -  new game", "F  -  flip board"):
        screen.blit(small.render(line, True, MUTED_TEXT), (x, y))
        y += 22


def draw_game_over(screen, title, subtitle=""):
    """Darken the board and show the result in the middle."""
    overlay = pygame.Surface((BOARD_WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    screen.blit(overlay, (0, 0))

    lines = [get_font(48).render(title, True, (200, 20, 20))]
    if subtitle:
        lines.append(get_font(26).render(subtitle, True, TEXT))
    lines.append(get_font(18).render("Press R to play again", True, MUTED_TEXT))

    box_w = max(line.get_width() for line in lines) + 80
    box_h = sum(line.get_height() for line in lines) + 14 * (len(lines) - 1) + 48
    box = pygame.Rect(0, 0, box_w, box_h)
    box.center = (BOARD_WIDTH // 2, HEIGHT // 2)
    pygame.draw.rect(screen, (250, 250, 250), box, border_radius=12)
    pygame.draw.rect(screen, (60, 60, 60), box, 2, border_radius=12)
    y = box.top + 24
    for line in lines:
        screen.blit(line, line.get_rect(midtop=(box.centerx, y)))
        y += line.get_height() + 14
