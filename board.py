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

def flip_coordinates(row, col):
    """Flip board coordinates for Black's perspective"""
    return 7 - row, 7 - col


def draw_board(screen, selected=None, valid_moves=[], turn="white"):
    for row in range(ROWS):
        for col in range(COLS):
            # Flip coordinates if it's Black's turn
            display_row = row if turn == "white" else 7 - row
            display_col = col if turn == "white" else 7 - col
            
            color = LIGHT if (row + col) % 2 == 0 else DARK

            if selected == (row, col):
                color = HIGHLIGHT

            pygame.draw.rect(
                screen,
                color,
                (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            )

    # draw move indicators
    for (r, c) in valid_moves:
        display_r = r if turn == "white" else 7 - r
        display_c = c if turn == "white" else 7 - c
        center = (
            display_c * SQUARE_SIZE + SQUARE_SIZE // 2,
            display_r * SQUARE_SIZE + SQUARE_SIZE // 2
        )
        pygame.draw.circle(screen, RED, center, 10)


def draw_pieces(screen, board, turn="white"):
    # Draw pieces as a colored circle with an uppercase letter centered.
    font = pygame.font.SysFont(None, SQUARE_SIZE // 2)
    radius = max(8, SQUARE_SIZE // 2 - 8)

    for row in range(ROWS):
        for col in range(COLS):
            piece = board[row][col]
            if piece == "":
                continue

            # Flip coordinates if it's Black's turn
            display_row = row if turn == "white" else 7 - row
            display_col = col if turn == "white" else 7 - col

            cx = display_col * SQUARE_SIZE + SQUARE_SIZE // 2
            cy = display_row * SQUARE_SIZE + SQUARE_SIZE // 2

            # White pieces: light fill, dark outline and dark letter.
            # Black pieces: dark fill, light outline and light letter.
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

            display_letter = piece.upper()
            text = font.render(display_letter, True, text_color)
            text_rect = text.get_rect(center=(cx, cy))
            screen.blit(text, text_rect)