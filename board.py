import pygame

# Settings
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
HIGHLIGHT = (0, 255, 0)
RED = (255, 0, 0)

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