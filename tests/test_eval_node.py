"""Tests for single node/line evaluation."""

import pytest

from src.v0.chess_tools.evaluation import find_stockfish
from src.v0.utils.eval_node import evaluate_node, evaluate_line, NodeEvaluation
from src.v0.utils.tree import expand_wildcards


# Skip all tests if Stockfish is not available
pytestmark = pytest.mark.skipif(
    find_stockfish() is None,
    reason="Stockfish not installed",
)


class TestEvaluateLine:
    """Tests for evaluate_line function."""

    def test_returns_node_evaluation(self):
        """Should return a NodeEvaluation dataclass."""
        result = evaluate_line(("e4", "e5"), depth=10)

        assert isinstance(result, NodeEvaluation)

    def test_starting_position_roughly_equal(self):
        """Empty line (starting position) should evaluate near 0."""
        result = evaluate_line((), depth=10)

        assert result.centipawns is not None
        assert -50 <= result.centipawns <= 50

    def test_line_is_preserved(self):
        """The input line should be preserved in the result."""
        moves = ("e4", "e5", "Nf3")
        result = evaluate_line(moves, depth=10)

        assert result.line == moves

    def test_fen_matches_position(self):
        """FEN should match the position after the moves."""
        result = evaluate_line(("e4",), depth=8)

        # After 1. e4, it's Black's turn
        assert " b " in result.fen
        # Pawn should be on e4
        assert "4P3" in result.fen

    def test_best_move_is_populated(self):
        """best_move should contain a valid SAN move."""
        result = evaluate_line(("e4", "e5"), depth=10)

        assert result.best_move != ""
        # Should be a reasonable move (at least 2 chars)
        assert len(result.best_move) >= 2

    def test_winning_position_has_high_eval(self):
        """A position where White wins material should have high centipawns."""
        # 1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6?? 4. Qxf7+ is mate
        # But before the mate move, let's check a position where White won a pawn
        # 1. e4 d5 2. exd5 - White won a pawn
        result = evaluate_line(("e4", "d5", "exd5"), depth=12)

        assert result.centipawns is not None
        assert result.centipawns > 50  # At least half a pawn advantage

    def test_evaluation_str_format(self):
        """evaluation_str should be formatted correctly."""
        result = evaluate_line(("e4", "e5"), depth=10)

        eval_str = result.evaluation_str
        # Should be like "+0.25" or "-0.10"
        assert eval_str[0] in "+-0" or eval_str.startswith("M")


class TestEvaluateNode:
    """Tests for evaluate_node function."""

    def test_evaluates_leaf_node(self):
        """Should evaluate a leaf node from a tree."""
        tree = expand_wildcards("1. e4 e5")
        leaf = tree.children[0].children[0]  # The e5 node

        result = evaluate_node(leaf, depth=10)

        assert isinstance(result, NodeEvaluation)
        assert result.fen == leaf.fen

    def test_node_evaluation_has_centipawns(self):
        """Evaluation should include centipawns for non-mate positions."""
        tree = expand_wildcards("1. d4 d5")
        leaf = tree.children[0].children[0]

        result = evaluate_node(leaf, depth=10)

        assert result.centipawns is not None


class TestNodeEvaluationDataclass:
    """Tests for NodeEvaluation dataclass properties."""

    def test_is_mate_false_for_normal_position(self):
        """is_mate should be False for normal positions."""
        result = evaluate_line(("e4", "e5"), depth=10)

        assert not result.is_mate
        assert result.mate_in is None

    def test_node_evaluation_is_frozen(self):
        """NodeEvaluation should be immutable."""
        result = evaluate_line(("e4",), depth=8)

        with pytest.raises(AttributeError):
            result.centipawns = 100


class TestMateDetection:
    """Tests for mate detection in node evaluation."""

    def test_mate_in_one_detected(self):
        """Should detect mate in 1."""
        # Scholar's mate position - White to play Qxf7#
        # 1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6?? and now 4. Qxf7#
        result = evaluate_line(("e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6"), depth=10)

        assert result.is_mate
        assert result.mate_in == 1
        assert result.centipawns is None

    def test_mate_evaluation_str(self):
        """evaluation_str should show mate notation."""
        result = evaluate_line(("e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6"), depth=10)

        assert "M" in result.evaluation_str
