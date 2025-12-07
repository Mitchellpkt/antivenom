"""Wildcard expansion for PGN-with-wildcards into opening trees."""

from __future__ import annotations

from dataclasses import dataclass

import chess

from .parser import parse_game_string_simple


@dataclass(frozen=True)
class MoveNode:
    """A node in the opening tree.

    Represents a position reached after a move, with all possible continuations
    as children. The root node has move=None.
    """

    move: str | None
    """SAN move that led to this position (None for root)."""

    fen: str
    """FEN string of the position after this move."""

    children: tuple[MoveNode, ...]
    """Child nodes representing possible continuations."""

    def flatten(self) -> list[tuple[str, ...]]:
        """Return all complete lines as tuples of SAN moves.

        Each tuple represents a path from the root to a leaf node.
        The root's move (None) is excluded from the output.

        Returns:
            List of tuples, each containing the SAN moves for one complete line.

        Example:
            >>> tree = expand_wildcards("1. e4 __")
            >>> lines = tree.flatten()
            >>> ("e4", "e5") in lines
            True
        """
        return self._flatten_recursive(prefix=())

    def _flatten_recursive(self, prefix: tuple[str, ...]) -> list[tuple[str, ...]]:
        """Recursively collect all lines from this node."""
        # Build current path (skip None moves, i.e., root)
        current = prefix + (self.move,) if self.move else prefix

        # If leaf node, return this line
        if not self.children:
            return [current] if current else [()]

        # Otherwise, collect all lines from children
        lines = []
        for child in self.children:
            lines.extend(child._flatten_recursive(current))
        return lines

    @property
    def line_count(self) -> int:
        """Total number of leaf positions (complete lines).

        Returns:
            Number of distinct lines in the tree.
        """
        if not self.children:
            return 1
        return sum(child.line_count for child in self.children)


def expand_wildcards(
    pgn_with_wildcards: str,
    wildcard_symbol: str = "__",
) -> MoveNode:
    """Expand a PGN-with-wildcards string into a tree of all variations.

    Parses the input and for each wildcard, branches into all legal moves
    at that position. Non-wildcard moves proceed as a single branch.

    Args:
        pgn_with_wildcards: PGN string where wildcard_symbol means "any legal move".
                           Example: "1. e4 __ 2. Nf3"
        wildcard_symbol: The symbol representing wildcards (default: "__").

    Returns:
        MoveNode tree with all expanded variations. The root node has move=None
        and represents the starting position.

    Example:
        >>> tree = expand_wildcards("1. e4 __")
        >>> tree.line_count
        20
        >>> tree.children[0].move
        'e4'
    """
    moves = parse_game_string_simple(s=pgn_with_wildcards, wildcard_symbol=wildcard_symbol)
    board = chess.Board()

    return MoveNode(
        move=None,
        fen=board.fen(),
        children=_expand_moves(board, moves),
    )


def _expand_moves(board: chess.Board, moves: list[str | None]) -> tuple[MoveNode, ...]:
    """Recursively expand moves into a tree.

    Args:
        board: Current board position.
        moves: Remaining moves to process (None = wildcard).

    Returns:
        Tuple of MoveNodes for the next level of the tree.
    """
    if not moves:
        return ()

    current_move, *remaining = moves

    if current_move is None:
        # Wildcard: branch into all legal moves
        children = []
        for legal_move in board.legal_moves:
            san = board.san(legal_move)
            new_board = board.copy()
            new_board.push(legal_move)
            children.append(
                MoveNode(
                    move=san,
                    fen=new_board.fen(),
                    children=_expand_moves(new_board, remaining),
                )
            )
        return tuple(children)
    else:
        # Specific move: single branch
        try:
            move = board.parse_san(current_move)
        except ValueError as e:
            raise ValueError(
                f"Illegal move '{current_move}' in position: {board.fen()}\n"
                f"The move is not legal in this position. This can happen when a "
                f"repertoire move becomes illegal after certain opponent responses."
            ) from e

        new_board = board.copy()
        new_board.push(move)
        return (
            MoveNode(
                move=current_move,
                fen=new_board.fen(),
                children=_expand_moves(new_board, remaining),
            ),
        )
