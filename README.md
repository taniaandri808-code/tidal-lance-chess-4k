# Tidal Lance — a 4 KB Python chess engine

Tidal Lance is a compact chess engine written in pure Python (standard library
only) for the [make.fun](https://make.fun) competition
[tiny-chess-01](https://make.fun/competitions/tiny-chess-01).

- `main.py` is the whole engine: a 10x12-mailbox board, full legal move
  generation (castling, en passant, promotions), an iterative-deepening
  negamax alpha-beta search with a fixed node budget, quiescence search,
  MVV-LVA / killer / history move ordering, a zobrist transposition table and
  an incrementally-updated material + piece-square evaluation with a bishop
  pair bonus. Mate, stalemate, repetition, fifty-move and insufficient-material
  scores are handled inside the search; no wall clock is ever read.
- It drives the competition env over HTTP (POST `/game`, `/move`) using only
  `urllib`, one game after another, and exits when every game is over.

[![tiny-chess-01](https://make.fun/badge/tiny-chess-01.svg)](https://make.fun/competitions/tiny-chess-01)
[![rank](https://make.fun/badge/tiny-chess-01/taniaandri808-code/tidal-lance-chess-4k/rank.svg)](https://make.fun/competitions/tiny-chess-01)
[![reward](https://make.fun/badge/tiny-chess-01/taniaandri808-code/tidal-lance-chess-4k/reward.svg)](https://make.fun/competitions/tiny-chess-01)

## License

SPDX-License-Identifier: MIT
