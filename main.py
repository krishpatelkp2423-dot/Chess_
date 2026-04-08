import pygame
import sys
from board import board, draw_board, draw_pieces, WIDTH, HEIGHT, SQUARE_SIZE, BLACK
from pieces import get_valid_moves, handle_click

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("My Chess Game")
    clock = pygame.time.Clock()

    selected = None
    valid_moves = []
    turn = "white"

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                selected, valid_moves, turn = handle_click(
                    board, event.pos, selected, turn, SQUARE_SIZE
                )
                if selected:
                    valid_moves = get_valid_moves(board, selected[0], selected[1])

        screen.fill(BLACK)
        draw_board(screen, selected, valid_moves)
        draw_pieces(screen, board)
        pygame.display.flip()

main()