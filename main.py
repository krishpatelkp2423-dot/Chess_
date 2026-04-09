import pygame
import sys
from board import board, draw_board, draw_pieces, draw_score, WIDTH, HEIGHT, SQUARE_SIZE, BLACK, score, SIDEBAR_WIDTH
from pieces import get_valid_moves, handle_click

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("My Chess Game")
    clock = pygame.time.Clock()

    selected = None
    valid_moves = []
    turn = "white"
    view_flipped = False

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                prev_turn = turn
                selected, valid_moves, turn, winner = handle_click(
                    board, event.pos, selected, turn, SQUARE_SIZE, score, flipped=view_flipped, screen=screen
                )
                if selected:
                    valid_moves = get_valid_moves(board, selected[0], selected[1])
                # If the turn changed (a move occurred) and there's no winner,
                # flip the board view so the next player sees their side at bottom.
                if prev_turn != turn and winner is None:
                    view_flipped = not view_flipped

                if winner is not None:
                    # draw final board + score then show winner message and exit
                    screen.fill(BLACK)
                    draw_board(screen, None, [], flipped=view_flipped)
                    draw_pieces(screen, board, flipped=view_flipped)
                    draw_score(screen, score)
                    font = pygame.font.SysFont("DejaVuSans.ttf", 48)
                    msg = f"{winner.capitalize()} wins!"
                    text = font.render(msg, True, (200, 20, 20))
                    rect = text.get_rect(center=(WIDTH // 2 - SIDEBAR_WIDTH // 2, HEIGHT // 2))
                    # draw a semi-transparent overlay behind the text
                    overlay = pygame.Surface((rect.width + 40, rect.height + 20), pygame.SRCALPHA)
                    overlay.fill((255, 255, 255, 200))
                    screen.blit(overlay, (rect.x - 20, rect.y - 10))
                    screen.blit(text, rect)
                    pygame.display.flip()
                    # keep the final screen on for 3s so user sees the result, then exit
                    pygame.time.wait(3000)
                    pygame.quit()
                    sys.exit()
                    

        screen.fill(BLACK)
        draw_board(screen, selected, valid_moves, flipped=view_flipped)
        draw_pieces(screen, board, flipped=view_flipped)
        # draw the score panel on the right
        draw_score(screen, score)
        pygame.display.flip()

main()