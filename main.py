import argparse
import random
import sys
import threading
import traceback

import pygame

from board import (board, reset_board, score, draw_board, draw_pieces, draw_sidebar, draw_game_over,
                   screen_to_board, WIDTH, HEIGHT, BLACK, WIN_SCORE)
from pieces import (get_legal_moves, get_all_legal_moves, apply_move, is_promotion, get_game_status,
                    find_king, color_of, other_color)
from ai import ReinforcementAgent
from promotion import prompt_promotion


class Game:
    def __init__(self, ai_color="black", think_time=2.0):
        # which side the AI plays ("white" or "black"), or None for two players
        self.ai_color = ai_color
        self.ai_agent = ReinforcementAgent(think_time=think_time)
        self.manual_flip = False
        self.game_number = 0
        self.new_game()

    def new_game(self):
        reset_board()
        score.reset()
        self.turn = "white"
        self.selected = None
        self.valid_moves = []
        self.last_move = None
        self.check_square = None
        self.status = ""
        self.result = None  # (title, subtitle) once the game is over
        self.ai_job = None
        self.game_number += 1  # lets us ignore an AI move from a game that was restarted

    @property
    def flipped(self):
        """True when Black should be shown at the bottom of the screen."""
        if self.ai_color is None:
            black_at_bottom = self.turn == "black"  # two players: whoever is moving sits at the bottom
        else:
            black_at_bottom = self.ai_color == "white"  # the human's pieces are at the bottom
        return black_at_bottom != self.manual_flip

    def is_human_turn(self):
        return self.result is None and self.turn != self.ai_color

    # ------------------------------------------------------------------
    # Player input
    # ------------------------------------------------------------------
    def handle_click(self, pos, screen):
        if not self.is_human_turn():
            return
        square = screen_to_board(pos[0], pos[1], self.flipped)
        if square is None:
            return  # clicked on the sidebar
        row, col = square
        piece = board[row][col]

        if self.selected is not None and square in self.valid_moves:
            move = (self.selected, square)
            promote_to = "q"
            if is_promotion(board, move):
                promote_to = prompt_promotion(screen, self.turn)
            self.make_move(move, promote_to)
        elif piece != "" and color_of(piece) == self.turn and square != self.selected:
            self.selected = square
            self.valid_moves = get_legal_moves(board, row, col)
        else:
            self.selected = None
            self.valid_moves = []

    # ------------------------------------------------------------------
    # Moves and game rules
    # ------------------------------------------------------------------
    def make_move(self, move, promote_to="q"):
        new_board, captured = apply_move(board, move, promote_to)
        board[:] = new_board
        mover = self.turn
        self.turn = other_color(mover)
        self.last_move = move
        self.selected = None
        self.valid_moves = []
        self.check_square = None
        self.status = ""

        winner = score.add(mover, captured)
        if winner is not None:
            self.result = (f"{winner.capitalize()} wins!", f"Reached {WIN_SCORE} points")
            return

        status = get_game_status(board, self.turn)
        if status in ("check", "checkmate"):
            self.check_square = find_king(board, self.turn)
        if status == "checkmate":
            self.result = ("Checkmate!", f"{mover.capitalize()} wins")
        elif status == "stalemate":
            self.result = ("Stalemate", "It's a draw")
        elif status == "check":
            self.status = "Check!"

    def update_ai(self):
        """Start the AI thinking on its turn, and play its move once it's ready.

        The AI thinks in a background thread so the window keeps responding
        (you can still move or close it while the computer is thinking).
        """
        if self.ai_color is None or self.result is not None or self.turn != self.ai_color:
            return

        if self.ai_job is None:
            job = {"game": self.game_number, "move": None, "done": False}
            position = [row[:] for row in board]
            white_points, black_points = score.white, score.black

            def think():
                try:
                    job["move"] = self.ai_agent.select_move(position, self.ai_color, white_points, black_points)
                except Exception:
                    traceback.print_exc()
                finally:
                    job["done"] = True

            self.ai_job = job
            threading.Thread(target=think, daemon=True).start()
            return

        if self.ai_job["done"]:
            job, self.ai_job = self.ai_job, None
            if job["game"] != self.game_number:
                return
            move = job["move"]
            if move is None:
                # Should not happen, but never leave the game stuck
                moves = get_all_legal_moves(board, self.turn)
                move = random.choice(moves) if moves else None
            if move is not None:
                self.make_move(move)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self, screen):
        screen.fill(BLACK)
        draw_board(screen, board, self.selected, self.valid_moves, self.flipped, self.last_move, self.check_square)
        draw_pieces(screen, board, self.flipped)
        status = self.status
        if self.ai_job is not None:
            status = (status + "\n" if status else "") + "AI thinking..."
        draw_sidebar(screen, score, self.turn, status, self.ai_color)
        if self.result is not None:
            draw_game_over(screen, *self.result)


def parse_args():
    parser = argparse.ArgumentParser(description="Chess with piece symbols and a computer opponent.")
    parser.add_argument("--ai", choices=["white", "black", "none"], default="black",
                        help="which side the computer plays (default: black). Use 'none' for two players.")
    parser.add_argument("--think-time", type=float, default=2.0,
                        help="most seconds the computer may think per move (default: 2)")
    return parser.parse_args()


def main():
    args = parse_args()
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("My Chess Game")
    clock = pygame.time.Clock()

    game = Game(ai_color=None if args.ai == "none" else args.ai, think_time=args.think_time)

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                game.handle_click(event.pos, screen)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.new_game()
                elif event.key == pygame.K_f:
                    game.manual_flip = not game.manual_flip

        game.update_ai()
        game.draw(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()
