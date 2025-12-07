"""Evaluation of single positions from move trees."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..chess_tools.evaluation import evaluate_fen, EvaluationResult

if TYPE_CHECKING:
    from .tree import MoveNode


@dataclass(frozen=True)
class NodeEvaluation:
    """Evaluation result for a single node/line."""

    line: tuple[str, ...]
    """The sequence of moves leading to this position."""

    fen: str
    """FEN of the evaluated position."""

    centipawns: int | None
    """Evaluation in centipawns from White's perspective (None if mate)."""

    mate_in: int | None
    """Moves until mate (positive=White mates, negative=Black mates)."""

    best_move: str
    """Best continuation in SAN notation."""

    @property
    def is_mate(self) -> bool:
        """Whether the position is a forced mate."""
        return self.mate_in is not None

    @property
    def evaluation_str(self) -> str:
        """Human-readable evaluation string."""
        if self.mate_in is not None:
            return f"M{self.mate_in}"
        elif self.centipawns is not None:
            return f"{self.centipawns / 100:+.2f}"
        return "?"


def evaluate_node(
    node: MoveNode,
    *,
    depth: int = 20,
    stockfish_path: str | None = None,
) -> NodeEvaluation:
    """Evaluate a single node from a move tree.

    Takes a MoveNode and returns its Stockfish evaluation along with
    the line that led to this position.

    Args:
        node: A MoveNode from an expanded tree (typically a leaf node).
        depth: Stockfish search depth.
        stockfish_path: Path to Stockfish binary (auto-detected if None).

    Returns:
        NodeEvaluation containing the line, position, and evaluation.

    Example:
        >>> tree = expand_wildcards("1. e4 __")
        >>> leaf = tree.children[0].children[0]  # e.g., 1. e4 e5
        >>> result = evaluate_node(leaf, depth=15)
        >>> print(f"{' '.join(result.line)}: {result.evaluation_str}")
    """
    # Get the line leading to this node by walking up isn't possible
    # with frozen dataclass, so we require the caller to track it
    # or we extract from a single leaf
    line = _extract_line_to_node(node)

    eval_result = evaluate_fen(
        node.fen,
        depth=depth,
        stockfish_path=stockfish_path,
    )

    return NodeEvaluation(
        line=line,
        fen=node.fen,
        centipawns=eval_result.centipawns,
        mate_in=eval_result.mate_in,
        best_move=eval_result.best_move,
    )


def evaluate_line(
    moves: tuple[str, ...],
    *,
    depth: int = 20,
    stockfish_path: str | None = None,
) -> NodeEvaluation:
    """Evaluate a position reached by a sequence of moves.

    Takes a tuple of SAN moves and returns the Stockfish evaluation
    of the final position.

    Args:
        moves: Tuple of SAN moves from the starting position.
        depth: Stockfish search depth.
        stockfish_path: Path to Stockfish binary (auto-detected if None).

    Returns:
        NodeEvaluation containing the line, position, and evaluation.

    Example:
        >>> result = evaluate_line(("e4", "e5", "Nf3"), depth=15)
        >>> print(f"{result.evaluation_str}")
    """
    import chess

    board = chess.Board()
    for move_san in moves:
        move = board.parse_san(move_san)
        board.push(move)

    eval_result = evaluate_fen(
        board.fen(),
        depth=depth,
        stockfish_path=stockfish_path,
    )

    return NodeEvaluation(
        line=moves,
        fen=board.fen(),
        centipawns=eval_result.centipawns,
        mate_in=eval_result.mate_in,
        best_move=eval_result.best_move,
    )


def _extract_line_to_node(node: MoveNode) -> tuple[str, ...]:
    """Extract the move sequence for a single-line tree branch.

    This only works reliably for leaf nodes or single-child paths.
    For nodes with multiple children, only returns the node's own move.
    """
    if node.move is None:
        return ()
    return (node.move,)
