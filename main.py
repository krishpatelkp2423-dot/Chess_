import pygame
import sys
from board import board, draw_board, draw_pieces, draw_score, WIDTH, HEIGHT, SQUARE_SIZE, BLACK, score, SIDEBAR_WIDTH
from pieces import get_valid_moves, handle_click
from ai import ReinforcementAgent, choose_ai_move

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("My Chess Game")
    clock = pygame.time.Clock()

    selected = None
    valid_moves = []
    turn = "white"
    # config: which side the AI plays ("white" or "black"), or None to disable
    AI_COLOR = "black"
    ai_agent = ReinforcementAgent()

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                prev_turn = turn
                selected, valid_moves, turn, winner = handle_click(
                    board, event.pos, selected, turn, SQUARE_SIZE, score, flipped=False, screen=screen
                )
                if selected:
                    valid_moves = get_valid_moves(board, selected[0], selected[1])

                if winner is not None:
                    print(f"[MAIN DEBUG] Player move winner detected: {winner}")
                    # draw final board + score then show winner message and exit
                    screen.fill(BLACK)
                    draw_board(screen, None, [], flipped=False)
                    draw_pieces(screen, board, flipped=False)
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
        draw_board(screen, selected, valid_moves, flipped=False)
        draw_pieces(screen, board, flipped=False)
        # draw the score panel on the right
        draw_score(screen, score)
        pygame.display.flip()

        # If AI is enabled and it's the AI's turn, have it play a move
        if AI_COLOR is not None and turn == AI_COLOR and winner is None:
            mv = ai_agent.select_move(board, AI_COLOR)
            if mv is not None:
                (r0, c0), (r1, c1) = mv
                # perform move
                captured = board[r1][c1]
                if captured != "" and score is not None:
                    winner = score.add(AI_COLOR, captured)
                    if winner is not None:
                        print(f"[MAIN DEBUG] AI move winner detected: {winner}")
                board[r1][c1] = board[r0][c0]
                board[r0][c0] = ""
                # handle promotion (basic): if pawn reached far rank promote to queen
                moved = board[r1][c1]
                if moved.lower() == "p":
                    if (moved.isupper() and r1 == 0) or (moved.islower() and r1 == 7):
                        board[r1][c1] = "Q" if moved.isupper() else "q"
                # switch turn
                turn = "black" if turn == "white" else "white"
                
                # Check if AI's move won the game
                if winner is not None:
                    print(f"[MAIN DEBUG] AI won! Displaying win screen for {winner}")
                    screen.fill(BLACK)
                    draw_board(screen, None, [], flipped=False)
                    draw_pieces(screen, board, flipped=False)
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

main()