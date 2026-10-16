"""Checks for the chess rules and the AI.

Run from the project folder with:  python -m unittest discover tests
"""
import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from board import START_POSITION, Score, WIN_SCORE  # noqa: E402
from pieces import apply_move, get_all_moves, get_valid_moves, other_color  # noqa: E402
from ai import choose_ai_move  # noqa: E402
import main  # noqa: E402


def empty_board():
    return [["" for _ in range(8)] for _ in range(8)]


def start_board():
    return [row[:] for row in START_POSITION]


def perft(board, color, depth):
    """Count every possible sequence of `depth` moves (a standard move generator test)."""
    moves = get_all_moves(board, color)
    if depth == 1:
        return len(moves)
    return sum(perft(apply_move(board, m)[0], other_color(color), depth - 1) for m in moves)


class RulesTest(unittest.TestCase):
    def test_move_counts_from_start(self):
        # Known correct answers for the starting position
        self.assertEqual(perft(start_board(), "white", 1), 20)
        self.assertEqual(perft(start_board(), "white", 2), 400)
        self.assertEqual(perft(start_board(), "white", 3), 8902)

    def test_king_can_be_captured(self):
        b = empty_board()
        b[7][4] = "K"
        b[0][4] = "r"  # black rook attacks the white king
        b[0][0] = "k"
        self.assertIn((7, 4), get_valid_moves(b, 0, 4))
        new_b, captured = apply_move(b, ((0, 4), (7, 4)))
        self.assertEqual(captured, "K")
        self.assertEqual(new_b[7][4], "r")

    def test_no_check_rules(self):
        # A king may move next to an attacking piece, and other pieces may
        # move even when their king is attacked.
        b = empty_board()
        b[7][4] = "K"  # e1
        b[6][4] = "R"  # e2
        b[0][4] = "r"  # e8
        b[0][3] = "r"  # d8
        b[0][0] = "k"
        self.assertIn((7, 3), get_valid_moves(b, 7, 4))
        self.assertIn((6, 0), get_valid_moves(b, 6, 4))

    def test_promotion(self):
        b = empty_board()
        b[1][0] = "P"
        b[6][7] = "p"
        new_b, _ = apply_move(b, ((1, 0), (0, 0)))
        self.assertEqual(new_b[0][0], "Q")
        new_b, _ = apply_move(b, ((1, 0), (0, 0)), promote_to="n")
        self.assertEqual(new_b[0][0], "N")
        new_b, _ = apply_move(b, ((1, 0), (0, 0)), promote_to="k")
        self.assertEqual(new_b[0][0], "K")
        new_b, _ = apply_move(b, ((6, 7), (7, 7)))
        self.assertEqual(new_b[7][7], "q")

    def test_apply_move_does_not_change_original(self):
        b = start_board()
        apply_move(b, ((6, 4), (4, 4)))
        self.assertEqual(b, START_POSITION)

    def test_score_race(self):
        s = Score()
        self.assertIsNone(s.add("white", "q"))
        self.assertIsNone(s.add("white", "r"))
        self.assertEqual(s.add("white", "p"), "white")
        self.assertEqual(s.white, WIN_SCORE)

    def test_king_is_worth_two_points(self):
        s = Score()
        s.add("black", "K")
        self.assertEqual(s.black, 2)


class GameTest(unittest.TestCase):
    def test_turn_is_skipped_when_a_player_cannot_move(self):
        game = main.Game(ai_color=None)
        b = main.board
        for r in range(8):
            for c in range(8):
                b[r][c] = ""
        b[1][0], b[1][2] = "p", "p"  # black pawns on a7 and c7...
        b[2][0], b[2][2] = "P", "P"  # ...blocked by white pawns, nothing to capture
        b[7][7] = "K"
        game.make_move(((7, 7), (7, 6)))  # White moves, Black can't, so it's White again
        self.assertEqual(game.turn, "white")
        self.assertIsNone(game.result)

    def test_reaching_15_points_wins(self):
        game = main.Game(ai_color=None)
        main.score.white = 13
        b = main.board
        b[1][4] = ""   # remove the e7 pawn
        b[2][4] = "Q"  # white queen on e6 can take the king on e8
        game.make_move(((2, 4), (0, 4)))  # the king is worth 2 points: 13 + 2 = 15
        self.assertEqual(game.result[0], "White wins!")


class AITest(unittest.TestCase):
    def test_plays_a_valid_move(self):
        b = start_board()
        move = choose_ai_move(b, "black", think_time=1.0)
        self.assertIn(move, get_all_moves(b, "black"))

    def test_no_move_when_it_has_no_moves(self):
        b = empty_board()
        b[1][0], b[1][2] = "p", "p"  # black pawns on a7 and c7, blocked
        b[2][0], b[2][2] = "P", "P"
        b[7][7] = "K"
        self.assertEqual(get_all_moves(b, "black"), [])
        self.assertIsNone(choose_ai_move(b, "black", think_time=1.0))

    def test_takes_the_king_to_win(self):
        # Black has 13 points: taking the white king (2 points) wins.
        b = empty_board()
        b[7][4] = "K"  # e1
        b[6][0] = "P"  # a2
        b[0][4] = "r"  # black rook on e8 can take the king
        b[0][0] = "k"
        self.assertEqual(choose_ai_move(b, "black", 0, 13, think_time=1.0), ((0, 4), (7, 4)))

    def test_takes_a_free_queen(self):
        b = start_board()
        b[4][4] = "Q"  # white queen left on e4
        b[7][3] = ""
        b[2][5] = "n"  # black knight on f6 attacks e4
        b[0][6] = ""
        move = choose_ai_move(b, "black", think_time=1.0)
        self.assertEqual(move[1], (4, 4))

    def test_knows_about_the_score_race(self):
        # Black's queen can take a rook that a pawn defends. Normally that
        # trade is bad, but with 10 points it reaches 15 and wins at once.
        b = empty_board()
        b[7][7] = "K"
        b[4][3] = "R"  # d4
        b[5][4] = "P"  # e3 defends d4
        b[0][0] = "k"
        b[0][3] = "q"  # d8
        self.assertEqual(choose_ai_move(b, "black", 0, 10, think_time=1.0), ((0, 3), (4, 3)))
        self.assertNotEqual(choose_ai_move(b, "black", 0, 0, think_time=1.0), ((0, 3), (4, 3)))


if __name__ == "__main__":
    unittest.main()
