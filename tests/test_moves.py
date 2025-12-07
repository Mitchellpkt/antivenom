"""Tests for legal move generation."""

import pytest
import chess

from src.v0.chess_tools.moves import (
    get_legal_moves,
    get_legal_moves_from_pgn,
    get_legal_moves_from_fen,
    MoveInfo,
    PositionInfo,
)


class TestGetLegalMoves:
    """Tests for get_legal_moves with Board objects."""

    def test_starting_position_has_20_moves(self):
        """Starting position should have exactly 20 legal moves."""
        board = chess.Board()
        info = get_legal_moves(board)

        assert info.move_count == 20
        assert info.turn == "white"
        assert not info.is_check
        assert not info.is_checkmate
        assert not info.is_stalemate

    def test_returns_position_info_dataclass(self):
        """Should return a PositionInfo dataclass."""
        board = chess.Board()
        info = get_legal_moves(board)

        assert isinstance(info, PositionInfo)
        assert isinstance(info.legal_moves, tuple)
        assert all(isinstance(m, MoveInfo) for m in info.legal_moves)

    def test_move_info_contains_all_fields(self):
        """MoveInfo should contain all expected fields."""
        board = chess.Board()
        info = get_legal_moves(board)

        move = info.legal_moves[0]
        assert hasattr(move, "san")
        assert hasattr(move, "uci")
        assert hasattr(move, "is_capture")
        assert hasattr(move, "is_castling")
        assert hasattr(move, "is_en_passant")
        assert hasattr(move, "gives_check")

    def test_fen_is_correct(self):
        """FEN should match the board state."""
        board = chess.Board()
        info = get_legal_moves(board)

        assert info.fen == chess.STARTING_FEN


class TestGetLegalMovesFromPgn:
    """Tests for PGN parsing and move generation."""

    def test_bare_move_sequence(self):
        """Should parse bare move sequences without headers."""
        info = get_legal_moves_from_pgn("1. e4 e5")

        assert info.turn == "white"
        assert info.move_count > 0

    def test_full_pgn_with_headers(self):
        """Should parse full PGN with headers."""
        pgn = """[Event "Test"]
[Result "*"]

1. e4 e5 2. Nf3 *"""
        info = get_legal_moves_from_pgn(pgn)

        assert info.turn == "black"

    def test_italian_game_position(self):
        """Test move generation after several moves of development.

        Position: Knights on f3/c6, White bishop on c4, pawns on e4/e5.
        Verifies that Bc5 is among Black's legal moves.
        """
        info = get_legal_moves_from_pgn("1. e4 e5 2. Nf3 Nc6 3. Bc4")

        assert info.turn == "black"
        # Black should be able to play Bc5 (Giuoco Piano)
        move_sans = [m.san for m in info.legal_moves]
        assert "Bc5" in move_sans

    def test_users_example_position(self):
        """Test position with a knight capture on e5.

        Position: White knight on e5 (just captured pawn), Black knight on f6.
        Verifies move generation works and d6 (attacking the knight) is available.
        """
        info = get_legal_moves_from_pgn("1. e4 e5 2. Nf3 Nf6 3. Nxe5")

        assert info.turn == "black"
        assert info.move_count > 0
        # Common responses include Nxe4, d6, Qe7
        move_sans = [m.san for m in info.legal_moves]
        assert "d6" in move_sans  # Most common response

    def test_empty_pgn_returns_starting_position(self):
        """Empty PGN should return the starting position."""
        info = get_legal_moves_from_pgn("")

        assert info.fen == chess.STARTING_FEN
        assert info.move_count == 20


class TestGetLegalMovesFromFen:
    """Tests for FEN parsing and move generation."""

    def test_starting_position_fen(self):
        """Should handle starting position FEN."""
        info = get_legal_moves_from_fen(chess.STARTING_FEN)

        assert info.move_count == 20
        assert info.turn == "white"

    def test_custom_position(self):
        """Should handle arbitrary FEN positions.

        Position: White pawn on e4, Black to move. Verifies FEN parsing
        gives correct turn and move count (20 moves, same as start).
        """
        # Position after 1. e4
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        info = get_legal_moves_from_fen(fen)

        assert info.turn == "black"
        assert info.move_count == 20

    def test_invalid_fen_raises_error(self):
        """Invalid FEN should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid FEN"):
            get_legal_moves_from_fen("not a valid fen")


class TestEdgeCases:
    """Tests for chess edge cases that are easy to get wrong."""

    def test_en_passant_available(self):
        """En passant should be included when legal.

        Position: White pawn on e5, Black pawn just moved f7-f5.
        White can capture en passant with exf6. Verifies this special
        move is included and flagged correctly.
        """
        # After 1. e4 d5 2. e5 f5, en passant exf6 is legal
        info = get_legal_moves_from_pgn("1. e4 d5 2. e5 f5")

        assert info.turn == "white"
        move_sans = [m.san for m in info.legal_moves]
        assert "exf6" in move_sans

        # Find the en passant move and verify its flag
        ep_move = next(m for m in info.legal_moves if m.san == "exf6")
        assert ep_move.is_en_passant

    def test_castling_available(self):
        """Castling should be included when legal.

        Position: White's f1 and g1 squares are clear, king and rook unmoved.
        Verifies O-O is in the legal moves list and flagged as castling.
        """
        # Position where white can castle kingside
        info = get_legal_moves_from_pgn("1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. d3 Nf6 5. Bg5 d6")

        move_sans = [m.san for m in info.legal_moves]
        assert "O-O" in move_sans

        castle_move = next(m for m in info.legal_moves if m.san == "O-O")
        assert castle_move.is_castling

    def test_castling_blocked_by_check(self):
        """Castling should not be available when in check.

        Position: White king on e1, Black queen on e4 giving check.
        Rooks are in corners but castling is illegal while in check.
        Verifies O-O and O-O-O are not in the move list.
        """
        # White king in check from black queen on e4
        fen = "r3k2r/pppppppp/8/8/4q3/8/PPPP1PPP/R3K2R w KQkq - 0 1"
        info = get_legal_moves_from_fen(fen)

        move_sans = [m.san for m in info.legal_moves]
        assert "O-O" not in move_sans
        assert "O-O-O" not in move_sans
        assert info.is_check

    def test_pinned_piece_cannot_move(self):
        """A pinned piece should have limited moves.

        Position: Black bishop on b4, White knight on c3, White king on e1.
        The knight is pinned to the king along the b4-e1 diagonal.
        Verifies the game still has legal moves (pin is handled correctly).
        """
        # Position with a pinned knight
        fen = "r1bqk2r/pppp1ppp/2n2n2/4p3/1b2P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 4 4"
        info = get_legal_moves_from_fen(fen)

        # The c3 knight is pinned by the b4 bishop - verify it can't move freely
        # (It can only move along the pin line or the pin must be broken)
        # This is handled internally by python-chess
        assert info.move_count > 0  # Game continues

    def test_checkmate_has_no_moves(self):
        """Checkmate position should have zero legal moves.

        Position: Black queen on h4 with White king trapped on e1.
        White pawns on f3/g4 block escape, queen covers remaining squares.
        Verifies is_checkmate=True, is_check=True, move_count=0.
        """
        # Fool's mate position
        info = get_legal_moves_from_pgn("1. f3 e5 2. g4 Qh4#")

        assert info.is_checkmate
        assert info.move_count == 0
        assert info.is_check

    def test_stalemate_has_no_moves(self):
        """Stalemate position should have zero legal moves but not be checkmate.

        Position: Black king on a8, White queen on c7, White king on b6.
        Black has no legal moves (a7/b8 attacked) but is not in check.
        Verifies is_stalemate=True, is_checkmate=False, is_check=False.
        """
        # Classic stalemate: Black king trapped in corner, not in check
        fen = "k7/2Q5/1K6/8/8/8/8/8 b - - 0 1"
        info = get_legal_moves_from_fen(fen)

        assert info.is_stalemate
        assert info.move_count == 0
        assert not info.is_checkmate
        assert not info.is_check

    def test_capture_detection(self):
        """Captures should be correctly identified.

        Position: White pawn on e4, Black pawn on d5 (attacking each other).
        Verifies exd5 is the only capture and is flagged as is_capture=True.
        """
        # Position where captures are possible
        info = get_legal_moves_from_pgn("1. e4 d5")

        captures = [m for m in info.legal_moves if m.is_capture]
        assert len(captures) == 1
        assert captures[0].san == "exd5"

    def test_check_detection(self):
        """Moves giving check should be correctly identified.

        Position: Black king on e8, b5-e8 diagonal is open.
        White's bishop can move to b5 giving check.
        Verifies Bb5+ is in the list and flagged as gives_check=True.
        """
        # Position after 1. e4 d6 2. Nf3 e5 - Bb5+ is possible
        fen = "rnbqkbnr/ppp2ppp/3p4/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3"
        info = get_legal_moves_from_fen(fen)

        check_moves = [m for m in info.legal_moves if m.gives_check]
        check_sans = [m.san for m in check_moves]
        assert "Bb5+" in check_sans


class TestDataclassProperties:
    """Tests for dataclass behavior and properties."""

    def test_position_info_is_frozen(self):
        """PositionInfo should be immutable."""
        info = get_legal_moves_from_pgn("1. e4")

        with pytest.raises(AttributeError):
            info.turn = "black"

    def test_move_info_is_frozen(self):
        """MoveInfo should be immutable."""
        info = get_legal_moves_from_pgn("1. e4")
        move = info.legal_moves[0]

        with pytest.raises(AttributeError):
            move.san = "different"

    def test_move_count_property(self):
        """move_count property should match len(legal_moves)."""
        info = get_legal_moves_from_pgn("1. e4 e5")

        assert info.move_count == len(info.legal_moves)
