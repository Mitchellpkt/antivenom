"""Tests for wildcard expansion into opening trees."""

import pytest
import chess

from src.v0.utils.tree import expand_wildcards, MoveNode


class TestExpandWildcards:
    """Tests for the expand_wildcards function."""

    def test_no_wildcards_single_line(self):
        """Input without wildcards produces a single-line tree."""
        tree = expand_wildcards("1. e4 e5 2. Nf3")

        assert tree.line_count == 1
        lines = tree.flatten()
        assert lines == [("e4", "e5", "Nf3")]

    def test_single_wildcard_expands_to_all_legal(self):
        """A single wildcard after e4 expands to all 20 legal Black responses."""
        tree = expand_wildcards("1. e4 __")

        assert tree.line_count == 20
        lines = tree.flatten()
        assert len(lines) == 20
        # All lines start with e4
        assert all(line[0] == "e4" for line in lines)
        # All lines have exactly 2 moves
        assert all(len(line) == 2 for line in lines)

    def test_wildcard_at_start_expands_white_moves(self):
        """Wildcard at move 1 expands to all 20 White first moves."""
        tree = expand_wildcards("1. __")

        assert tree.line_count == 20

    def test_multiple_wildcards_multiply(self):
        """Two wildcards produce n1 * n2 lines."""
        # 1. __ __ gives 20 * 20 = 400 lines
        tree = expand_wildcards("1. __ __")

        assert tree.line_count == 400

    def test_wildcard_followed_by_fixed_move(self):
        """Wildcard followed by a fixed move works correctly."""
        tree = expand_wildcards("1. e4 __ 2. Nf3")

        # 20 responses to e4, each followed by Nf3
        assert tree.line_count == 20
        lines = tree.flatten()
        # All lines end with Nf3
        assert all(line[-1] == "Nf3" for line in lines)
        # All lines have 3 moves
        assert all(len(line) == 3 for line in lines)

    def test_empty_input_returns_root_only(self):
        """Empty input returns just the root node with starting position."""
        tree = expand_wildcards("")

        assert tree.move is None
        assert tree.fen == chess.STARTING_FEN
        assert tree.children == ()
        assert tree.line_count == 1
        assert tree.flatten() == [()]


class TestMoveNode:
    """Tests for MoveNode dataclass."""

    def test_root_has_none_move(self):
        """Root node should have move=None."""
        tree = expand_wildcards("1. e4")

        assert tree.move is None

    def test_children_have_san_moves(self):
        """Child nodes should have SAN notation moves."""
        tree = expand_wildcards("1. e4 e5")

        assert tree.children[0].move == "e4"
        assert tree.children[0].children[0].move == "e5"

    def test_fen_is_correct(self):
        """FEN should reflect the position after each move."""
        tree = expand_wildcards("1. e4")

        # Root is starting position
        assert tree.fen == chess.STARTING_FEN
        # After e4
        e4_node = tree.children[0]
        expected_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        assert e4_node.fen == expected_fen

    def test_node_is_frozen(self):
        """MoveNode should be immutable."""
        tree = expand_wildcards("1. e4")

        with pytest.raises(AttributeError):
            tree.move = "d4"


class TestFlatten:
    """Tests for the flatten method."""

    def test_flatten_returns_complete_lines(self):
        """Flatten should return complete move sequences."""
        tree = expand_wildcards("1. e4 e5 2. Nf3 Nc6")

        lines = tree.flatten()
        assert lines == [("e4", "e5", "Nf3", "Nc6")]

    def test_flatten_excludes_root_none(self):
        """Flatten should not include the root's None move."""
        tree = expand_wildcards("1. e4")

        lines = tree.flatten()
        assert lines == [("e4",)]
        assert None not in lines[0]

    def test_flatten_with_wildcards(self):
        """Flatten correctly handles expanded wildcards."""
        tree = expand_wildcards("1. e4 __")

        lines = tree.flatten()
        # e5 should be one of the responses
        assert ("e4", "e5") in lines
        # d5 (Scandinavian) should also be there
        assert ("e4", "d5") in lines


class TestLineCount:
    """Tests for line_count property."""

    def test_line_count_matches_flatten_length(self):
        """line_count should equal len(flatten())."""
        tree = expand_wildcards("1. e4 __ 2. d4")

        assert tree.line_count == len(tree.flatten())

    def test_line_count_single_line(self):
        """Single line should have count of 1."""
        tree = expand_wildcards("1. e4 e5")

        assert tree.line_count == 1

    def test_line_count_empty(self):
        """Empty tree should have count of 1 (the empty line)."""
        tree = expand_wildcards("")

        assert tree.line_count == 1


class TestRealRepertoires:
    """Tests using real repertoire patterns."""

    def test_accelerated_london(self):
        """Test the accelerated London system pattern."""
        tree = expand_wildcards("1. d4 __ 2. Bf4 __")

        # After 1. d4, there are 20 legal responses
        # After each, 2. Bf4 is played, but the number of legal responses varies
        # (different positions after different Black first moves)
        assert tree.line_count > 400  # At least 20 * 20, usually more

        lines = tree.flatten()
        # All lines should be 4 moves
        assert all(len(line) == 4 for line in lines)
        # All lines should have d4 first, Bf4 third
        assert all(line[0] == "d4" and line[2] == "Bf4" for line in lines)

    def test_sicilian_repertoire(self):
        """Test a White anti-Sicilian repertoire pattern."""
        # 1. e4 __ 2. Nc3 - Closed Sicilian idea (always legal)
        tree = expand_wildcards("1. e4 __ 2. Nc3")

        # 20 Black responses to e4, each followed by Nc3
        assert tree.line_count == 20
        lines = tree.flatten()
        assert all(line[0] == "e4" and line[2] == "Nc3" for line in lines)


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_wildcard_at_end(self):
        """Wildcard as the last move should expand correctly."""
        tree = expand_wildcards("1. e4 e5 2. __")

        # After 1. e4 e5, White has 29 legal moves
        assert tree.line_count == 29

    def test_custom_wildcard_symbol(self):
        """Should support custom wildcard symbols."""
        tree = expand_wildcards("1. e4 ?? 2. Nf3", wildcard_symbol="??")

        assert tree.line_count == 20

    def test_invalid_move_raises_error(self):
        """Invalid SAN move should raise ValueError with clear message."""
        with pytest.raises(ValueError, match=r"(?s)Illegal move.*not legal in this position"):
            expand_wildcards("1. e4 e5 2. Qh5 Qxh5")  # Qxh5 is illegal

    def test_consecutive_wildcards(self):
        """Multiple consecutive wildcards should work."""
        tree = expand_wildcards("1. __ __ __")

        # First wildcard: 20 moves
        # Second wildcard: 20 responses each
        # Third wildcard: varies by position
        assert tree.line_count > 0
        lines = tree.flatten()
        assert all(len(line) == 3 for line in lines)
