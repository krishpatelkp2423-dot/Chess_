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


score = Score()

def draw_board(screen, selected=None, valid_moves=[]):
    for row in range(ROWS):
        for col in range(COLS):
            color = LIGHT if (row + col) % 2 == 0 else DARK

            if selected == (row, col):
                color = HIGHLIGHT

            pygame.draw.rect(
                screen,
                color,
                (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            )

    # draw move indicators
    for (r, c) in valid_moves:
        center = (
            c * SQUARE_SIZE + SQUARE_SIZE // 2,
            r * SQUARE_SIZE + SQUARE_SIZE // 2
        )
        pygame.draw.circle(screen, RED, center, 10)


def draw_pieces(screen, board):
    font = pygame.font.SysFont("DejaVuSans.ttf", SQUARE_SIZE - 10)

    # Render the piece letters directly (e.g. 'K', 'p') instead of Unicode symbols.
    # Previously this used a mapping from letters to chess glyphs; we no longer need it.

    for row in range(ROWS):
        for col in range(COLS):
            piece = board[row][col]

            if piece != "":
                # Use the letter on the board directly as the symbol
                symbol = piece
                color = BLACK if piece.islower() else WHITE

                text = font.render(symbol, True, color)

                # center the piece in the square
                text_rect = text.get_rect(center=(
                    col * SQUARE_SIZE + SQUARE_SIZE // 2,
                    row * SQUARE_SIZE + SQUARE_SIZE // 2
                ))

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