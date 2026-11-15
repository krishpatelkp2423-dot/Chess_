"""Let the computer play against itself and report what happened.

Two copies of the AI play each other at different search depths (how many
moves ahead each one looks). This measures how much looking further ahead
helps, and shows what games look like under the 15-point rules.

Run from the project folder:

    python selfplay.py                 # depth 3 vs depth 1, 40 games
    python selfplay.py --a 2 --b 1 --games 100 --seed 7

Everything is repeatable: the searches are limited by depth, not by time,
and the only randomness is the four opening moves, which come from --seed.
Every opening is played twice with the sides swapped, so neither depth
gets the easier openings.
"""
import argparse
import os
import random
import statistics

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # board.py imports pygame; no window is needed

from board import START_POSITION, Score, WIN_SCORE  # noqa: E402
from pieces import apply_move, get_all_moves, other_color  # noqa: E402
from ai import choose_ai_move, position_key  # noqa: E402

MAX_MOVES = 400       # a game still going after this many moves counts as unfinished
NO_TIME_LIMIT = 1e9   # seconds; the search stops at its depth instead


def random_opening(rng):
    """Four random opening moves (two per side), none of them captures."""
    board = [row[:] for row in START_POSITION]
    color = "white"
    moves = []
    for _ in range(4):
        quiet = [m for m in get_all_moves(board, color) if board[m[1][0]][m[1][1]] == ""]
        move = rng.choice(quiet)
        board, _ = apply_move(board, move)
        moves.append(move)
        color = other_color(color)
    return moves


def play_game(depths, opening):
    """Play one game. `depths` is {"white": depth, "black": depth}.

    Returns (result, moves_played, points) where result is "white", "black",
    "draw" or "unfinished" and points is {"white": n, "black": n}.
    """
    board = [row[:] for row in START_POSITION]
    points = {"white": 0, "black": 0}
    turn = "white"
    seen = {position_key(board, turn): 1}  # how many times each position has come up
    for move_number in range(MAX_MOVES):
        if move_number < len(opening):
            move = opening[move_number]
        else:
            move = choose_ai_move(board, turn, points["white"], points["black"],
                                  depth=depths[turn], think_time=NO_TIME_LIMIT, seen=seen)
        board, captured = apply_move(board, move)
        if captured:
            points[turn] += Score.PIECE_VALUES[captured.lower()]
            if points[turn] >= WIN_SCORE:
                return turn, move_number + 1, points
        # A player with no possible moves skips their turn
        if get_all_moves(board, other_color(turn)):
            turn = other_color(turn)
        elif not get_all_moves(board, turn):
            return "draw", move_number + 1, points
        key = position_key(board, turn)
        seen[key] = seen.get(key, 0) + 1
    return "unfinished", MAX_MOVES, points


def main():
    parser = argparse.ArgumentParser(description="Play the chess AI against itself.")
    parser.add_argument("--a", type=int, default=3, help="search depth of player A (default: 3)")
    parser.add_argument("--b", type=int, default=1, help="search depth of player B (default: 1)")
    parser.add_argument("--games", type=int, default=40, help="games to play (default: 40)")
    parser.add_argument("--seed", type=int, default=1, help="seed for the random openings (default: 1)")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    wins = {"a": 0, "b": 0, "draw": 0, "unfinished": 0}
    white_wins = 0
    lengths = []
    for _ in range(args.games // 2):
        opening = random_opening(rng)
        for a_is_white in (True, False):
            depths = {"white": args.a if a_is_white else args.b,
                      "black": args.b if a_is_white else args.a}
            result, moves, _ = play_game(depths, opening)
            if result in ("draw", "unfinished"):
                wins[result] += 1
                continue
            lengths.append(moves)
            white_wins += result == "white"
            wins["a" if (result == "white") == a_is_white else "b"] += 1
            print(".", end="", flush=True)

    played = sum(wins.values())
    print(f"\nDepth {args.a} vs depth {args.b}: {played} games, seed {args.seed}")
    print(f"  depth {args.a} won {wins['a']}, depth {args.b} won {wins['b']}, "
          f"draws {wins['draw']}, unfinished {wins['unfinished']}")
    if lengths:
        print(f"  White won {white_wins} of the {len(lengths)} finished games")
        print(f"  game length: median {statistics.median(lengths):g} moves (both sides counted), "
              f"shortest {min(lengths)}, longest {max(lengths)}")


if __name__ == "__main__":
    main()
