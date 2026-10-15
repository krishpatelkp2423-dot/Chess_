"""Checks for the chess rules and the AI.

Run from the project folder with:  python -m unittest discover tests
"""
import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from board import START_POSITION, Score, WIN_SCORE  # noqa: E402
from pieces import (apply_move, get_all_legal_moves, get_game_status, get_legal_moves,  # noqa: E402
                    other_color)
from ai import choose_ai_move  # noqa: E402


def empty_board():
    return [["" for _ in range(8)] for _ in range(8)]


def start_board():
    return [row[:] for row in START_POSITION]


def perft(board, color, depth):
    """Count every possible sequence of `depth` moves (a standard move generator test)."""
    moves = get_all_legal_moves(board, color)
    if depth == 1:
        return len(moves)
    return sum(perft(apply_move(board, m)[0], other_color(color), depth - 1) for m in moves)


class RulesTest(unittest.TestCase):
    def test_move_counts_from_start(self):
        # Known correct answers for the starting position
        self.assertEqual(perft(start_board(), "white", 1), 20)
        self.assertEqual(perft(start_board(), "white", 2), 400)
        self.assertEqual(perft(start_board(), "white", 3), 8902)

    def test_fools_mate_is_checkmate(self):
        b = start_board()
        for move in [((6, 5), (5, 5)), ((1, 4), (3, 4)), ((6, 6), (4, 6)), ((0, 3), (4, 7))]:
            b, _ = apply_move(b, move)
        self.assertEqual(get_game_status(b, "white"), "checkmate")

    def test_stalemate(self):
        b = empty_board()
        b[0][7] = "k"  # black king h8
        b[2][6] = "Q"  # white queen g6
        b[1][5] = "K"  # white king f7
        self.assertEqual(get_game_status(b, "black"), "stalemate")

    def test_check(self):
        b = empty_board()
        b[7][4] = "K"
        b[0][4] = "r"
        b[0][0] = "k"
        self.assertEqual(get_game_status(b, "white"), "check")
        # every legal move must get the king out of the rook's line
        for (_, _), (r, c) in get_all_legal_moves(b, "white"):
            self.assertNotEqual(c, 4)

    def test_pinned_piece_cannot_leave_the_line(self):
        b = empty_board()
        b[7][4] = "K"  # white king e1
        b[6][4] = "R"  # white rook e2, pinned
        b[0][4] = "r"  # black rook e8
        b[0][0] = "k"
        moves = get_legal_moves(b, 6, 4)
        self.assertTrue(moves)
        self.assertTrue(all(c == 4 for r, c in moves))
        self.assertIn((0, 4), moves)  # can capture the pinning rook

    def test_king_cannot_walk_into_check(self):
        b = empty_board()
        b[7][4] = "K"  # e1
        b[0][3] = "r"  # black rook on the d-file
        b[0][7] = "k"
        moves = get_legal_moves(b, 7, 4)
        self.assertNotIn((7, 3), moves)
        self.assertNotIn((6, 3), moves)
        self.assertIn((6, 4), moves)

    def test_promotion(self):
        b = empty_board()
        b[1][0] = "P"
        b[6][7] = "p"
        new_b, _ = apply_move(b, ((1, 0), (0, 0)))
        self.assertEqual(new_b[0][0], "Q")
        new_b, _ = apply_move(b, ((1, 0), (0, 0)), promote_to="n")
        self.assertEqual(new_b[0][0], "N")
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


class AITest(unittest.TestCase):
    def test_plays_a_legal_move(self):
        b = start_board()
        move = choose_ai_move(b, "black", think_time=1.0)
        self.assertIn(move, get_all_legal_moves(b, "black"))

    def test_no_move_when_checkmated(self):
        b = start_board()
        for move in [((6, 5), (5, 5)), ((1, 4), (3, 4)), ((6, 6), (4, 6)), ((0, 3), (4, 7))]:
            b, _ = apply_move(b, move)
        self.assertIsNone(choose_ai_move(b, "white", think_time=1.0))

    def test_finds_mate_in_one(self):
        # Back-rank mate: Ra1-a8#
        b = empty_board()
        b[7][6] = "K"
        b[6][5], b[6][6], b[6][7] = "P", "P", "P"
        b[7][0] = "R"
        b[0][6] = "k"
        b[1][5], b[1][6], b[1][7] = "p", "p", "p"
        self.assertEqual(choose_ai_move(b, "white", think_time=1.0), ((7, 0), (0, 0)))

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
