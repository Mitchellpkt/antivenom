from typing import Any

def parse_game_string_simple(*, s: str, wildcard_symbol: str) -> list[str | None]:
    """ Converts PGN-with-wildcards strings to move lists in order of ply

    Wildcard symbols get parsed as None

    for example, if `__` is the wildcard, then

    `1. e4 e5 2. __ d5 3. __ h3`

    should get parsed as

    ["e4", "e5", None, "d5", None, "h3"]

    """
    tokens = s.split()
    moves = []
    for token in tokens:
        if token.endswith('.') and token[:-1].isdigit():
            continue
        moves.append(None if token == wildcard_symbol else token)
    return moves