This is a hacky hobby project for finding optimal moves *if you know that your opponent is going to play a particular system*, which may be different from optimal moves if your adversary is fully unconstrained

Systems are entered as PGN with wildcards, e.g.

`1. __ f6 2. __ c6 3. __`

The goal is to exhaustively enumerate combinations of legal moves, and identify those leading to optimal engine evals for the wildcard player
