import pygame

# Settings
# Keep the board area square and add a right-hand sidebar for score/ui
BOARD_WIDTH = 800
SIDEBAR_WIDTH = 200
WIDTH, HEIGHT = BOARD_WIDTH + SIDEBAR_WIDTH, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = BOARD_WIDTH // COLS

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
HIGHLIGHT = (0, 255, 0)
RED = (255, 0, 0)
SIDEBAR_BG = (230, 230, 230)


_PIECE_FONT_PATH = None
def _get_piece_font(size):
    """Return a pygame Font object that supports chess unicode glyphs when possible.
    Tries a list of common fonts that include the chess symbols and falls back
    to the default pygame font (which may not support the glyphs).
    """
    global _PIECE_FONT_PATH
    # If we already selected a font path, reuse it
    if _PIECE_FONT_PATH is not None:
        try:
            return pygame.font.Font(_PIECE_FONT_PATH, size)
        except Exception:
            _PIECE_FONT_PATH = None

    # Candidate font family names known to include chess glyphs on some systems
    candidates = [
        "DejaVuSans", "DejaVu Sans", "FreeSerif", "Symbola",
        "Noto Sans Symbols2", "Apple Symbols", "Arial Unicode MS", "Segoe UI Symbol"
    ]

    for name in candidates:
        path = pygame.font.match_font(name)
        if path:
            try:
                f = pygame.font.Font(path, size)
                # quick smoke-test: try rendering a king symbol
                f.render("\u265A", True, (0,0,0))
                _PIECE_FONT_PATH = path
                return f
            except Exception:
                continue

    # fallback
    return pygame.font.SysFont(None, size)

# Board layout
board = [
    ["r", "n", "b", "q", "k", "b", "n", "r"],
    ["p", "p", "p", "p", "p", "p", "p", "p"],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["P", "P", "P", "P", "P", "P", "P", "P"],
    ["R", "N", "B", "Q", "K", "B", "N", "R"],
]


# Piece values for scoring
class Score:
    PIECE_VALUES = {
        "p": 1,
        "n": 3,
        "b": 3,
        "r": 5,
        "q": 9,
        "k": 2,
    }

    def __init__(self):
        self.white = 0
        self.black = 0

    def add(self, capturing_color, piece_char):
        """Add the value of piece_char to capturing_color ('white' or 'black')."""
        if not piece_char:
            return
        value = self.PIECE_VALUES.get(piece_char.lower(), 0)
        if capturing_color == "white":
            self.white += value
        else:
            self.black += value

        # return winner if threshold reached (first to 15 wins)
        if self.white >= 15:
            return "white"
        if self.black >= 15:
            return "black"

        return None


score = Score()


def flip_board_view():
    """Rotate the internal `board` 180 degrees in-place so the next player
    sees their side at the bottom. This mutates the shared `board` list so
    callers (like `main.py`) don't need to rebind the name.
    """
    global board
    new = [row[::-1] for row in board[::-1]]
    board[:] = new

def draw_board(screen, selected=None, valid_moves=[], flipped=False):
    """Draw board; if flipped=True, render a 180° rotated view (screen coords
    map to board[7-row][7-col]). valid_moves and selected are in board
    coordinates and will be mapped to the screen when flipped."""
    for screen_r in range(ROWS):
        for screen_c in range(COLS):
            # compute which board cell to read
            if not flipped:
                row, col = screen_r, screen_c
            else:
                row, col = 7 - screen_r, 7 - screen_c

            color = LIGHT if (row + col) % 2 == 0 else DARK

            if selected == (row, col):
                color = HIGHLIGHT

            pygame.draw.rect(
                screen,
                color,
                (screen_c * SQUARE_SIZE, screen_r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            )

    # draw move indicators (map board coords to screen coords when flipped)
    for (r, c) in valid_moves:
        if not flipped:
            screen_r, screen_c = r, c
        else:
            screen_r, screen_c = 7 - r, 7 - c

        center = (
            screen_c * SQUARE_SIZE + SQUARE_SIZE // 2,
            screen_r * SQUARE_SIZE + SQUARE_SIZE // 2
        )
        pygame.draw.circle(screen, RED, center, 10)


def draw_pieces(screen, board, flipped=False):
    font = _get_piece_font(SQUARE_SIZE - 10)

    # Render the piece letters directly (e.g. 'K', 'p') instead of Unicode symbols.
    # Previously this used a mapping from letters to chess glyphs; we no longer need it.

    for board_r in range(ROWS):
        for board_c in range(COLS):
            piece = board[board_r][board_c]

            if piece != "":
                # determine where to draw on screen
                if not flipped:
                    screen_r, screen_c = board_r, board_c
                else:
                    screen_r, screen_c = 7 - board_r, 7 - board_c

        # Fallback reliable rendering: draw a simple circular piece icon with a letter
        # This avoids depending on system fonts that may not include chess glyphs.
        font = pygame.font.SysFont(None, SQUARE_SIZE // 2)
        radius = SQUARE_SIZE // 2 - 8

        for board_r in range(ROWS):
            for board_c in range(COLS):
                piece = board[board_r][board_c]

                if piece != "":
                    # determine where to draw on screen
                    if not flipped:
                        screen_r, screen_c = board_r, board_c
                    else:
                        screen_r, screen_c = 7 - board_r, 7 - board_c

                    cx = screen_c * SQUARE_SIZE + SQUARE_SIZE // 2
                    cy = screen_r * SQUARE_SIZE + SQUARE_SIZE // 2

                    # piece background: white pieces get light fill with black border,
                    # black pieces get dark fill with white border
                    if piece.isupper():
                        fill = WHITE
                        outline = (50, 50, 50)
                        text_color = (20, 20, 20)
                    else:
                        fill = (30, 30, 30)
                        outline = (200, 200, 200)
                        text_color = WHITE

                    pygame.draw.circle(screen, fill, (cx, cy), radius)
                    pygame.draw.circle(screen, outline, (cx, cy), radius, 2)

                    # draw the piece letter (uppercase) on top
                    display_letter = piece.upper()
                    text = font.render(display_letter, True, text_color)
                    text_rect = text.get_rect(center=(cx, cy))
                    screen.blit(text, text_rect)


def draw_score(screen, score):
    """Draw a simple score panel in the sidebar on the right."""
    font_title = pygame.font.SysFont("DejaVuSans.ttf", 28)
    font = pygame.font.SysFont("DejaVuSans.ttf", 24)

    # draw sidebar background so text is visible regardless of main fill
    pygame.draw.rect(screen, SIDEBAR_BG, (BOARD_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT))

    x = BOARD_WIDTH + 20
    y = 20

    title = font_title.render("Score", True, BLACK)
    screen.blit(title, (x, y))

    y += 40
    white_text = font.render(f"White: {score.white}", True, BLACK)
    screen.blit(white_text, (x, y))

    y += 30
    black_text = font.render(f"Black: {score.black}", True, BLACK)
    screen.blit(black_text, (x, y))

    # Show piece values as a legend
    y += 50
    legend_title = font.render("Values:", True, BLACK)
    screen.blit(legend_title, (x, y))
    y += 25
    for p, v in Score.PIECE_VALUES.items():
        line = font.render(f"{p.upper()}: {v}", True, BLACK)
        screen.blit(line, (x, y))
        y += 22