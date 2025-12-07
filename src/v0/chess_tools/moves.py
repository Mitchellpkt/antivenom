"""Legal move generation from PGN strings and FEN positions."""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import TYPE_CHECKING

import chess
import chess.pgn

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class MoveInfo:
    """Information about a legal move."""

    san: str
    """Standard Algebraic Notation (e.g., 'Nf3', 'O-O', 'exd5')."""

    uci: str
    """Universal Chess Interface notation (e.g., 'g1f3', 'e1g1', 'e4d5')."""

    is_capture: bool
    """Whether this move captures a piece."""

    is_castling: bool
    """Whether this move is castling."""

    is_en_passant: bool
    """Whether this move is an en passant capture."""

    gives_check: bool
    """Whether this move puts the opponent in check."""


@dataclass(frozen=True)
class PositionInfo:
    """Information about a chess position and its legal moves."""

    fen: str
    """FEN string representing the position."""

    turn: str
    """Which side is to move ('white' or 'black')."""

    is_check: bool
    """Whether the side to move is in check."""

    is_checkmate: bool
    """Whether the position is checkmate."""

    is_stalemate: bool
    """Whether the position is stalemate."""

    legal_moves: tuple[MoveInfo, ...]
    """All legal moves in this position."""

    @property
    def move_count(self) -> int:
        """Number of legal moves available."""
        return len(self.legal_moves)


def get_legal_moves(board: chess.Board) -> PositionInfo:
    """
    Get all legal moves for a chess.Board position.

    Args:
        board: A python-chess Board object.

    Returns:
        PositionInfo containing position details and all legal moves.

    Example:
        >>> import chess
        >>> board = chess.Board()
        >>> info = get_legal_moves(board)
        >>> info.move_count
        20
    """
    legal_moves = []
    for move in board.legal_moves:
        legal_moves.append(
            MoveInfo(
                san=board.san(move),
                uci=move.uci(),
                is_capture=board.is_capture(move),
                is_castling=board.is_castling(move),
                is_en_passant=board.is_en_passant(move),
                gives_check=board.gives_check(move),
            )
        )

    return PositionInfo(
        fen=board.fen(),
        turn="white" if board.turn == chess.WHITE else "black",
        is_check=board.is_check(),
        is_checkmate=board.is_checkmate(),
        is_stalemate=board.is_stalemate(),
        legal_moves=tuple(legal_moves),
    )


def get_legal_moves_from_pgn(pgn: str) -> PositionInfo:
    """
    Parse a PGN string and get all legal moves for the resulting position.

    Accepts either full PGN with headers or bare move sequences.

    Args:
        pgn: A PGN string (e.g., "1. e4 e5 2. Nf3 Nc6" or full PGN with headers).

    Returns:
        PositionInfo containing position details and all legal moves.

    Raises:
        ValueError: If the PGN cannot be parsed or contains illegal moves.

    Example:
        >>> info = get_legal_moves_from_pgn("1. e4 e5 2. Nf3 Nc6")
        >>> info.turn
        'white'
        >>> any(m.san == "Bb5" for m in info.legal_moves)
        True
    """
    board = _parse_pgn_to_board(pgn)
    return get_legal_moves(board)


def get_legal_moves_from_fen(fen: str) -> PositionInfo:
    """
    Get all legal moves for a position specified by FEN.

    Args:
        fen: A FEN string representing the position.

    Returns:
        PositionInfo containing position details and all legal moves.

    Raises:
        ValueError: If the FEN is invalid.

    Example:
        >>> info = get_legal_moves_from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
        >>> info.turn
        'black'
    """
    try:
        board = chess.Board(fen)
    except ValueError as e:
        raise ValueError(f"Invalid FEN: {e}") from e

    return get_legal_moves(board)


def _parse_pgn_to_board(pgn: str) -> chess.Board:
    """
    Parse a PGN string and return the resulting board position.

    Handles both full PGN with headers and bare move sequences.
    """
    pgn = pgn.strip()

    # If it doesn't look like full PGN (no headers), wrap it
    if not pgn.startswith("["):
        pgn = f'[Result "*"]\n\n{pgn} *'

    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        raise ValueError("Failed to parse PGN: no game found")

    board = game.board()

    for move in game.mainline_moves():
        board.push(move)

    return board
