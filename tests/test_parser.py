from src.v0.utils.parser import parse_game_string_simple
import pytest

def test_parse_game_string_simple():
    """
    `1. e4 e5 2. __ d5 3. __ h3`

    should get parsed as

    ["e4", "e5", None, "d5", None, "h3"]
    """

    w = parse_game_string_simple(
        s="1. e4 e5 2. __ d5 3. __ h3",
        wildcard_symbol="__"
    )
    assert w == ["e4", "e5", None, "d5", None, "h3"]