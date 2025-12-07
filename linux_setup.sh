#!/usr/bin/env bash

set -e

# Install Stockfish
sudo apt update
sudo apt install -y stockfish

#---------------
# Package setup

## Install package in dev mode
#pip install -e ".[dev]"
#
## Verify installation
#python -c "from chess_tools import get_legal_moves_from_pgn; print('✓ chess_tools installed')"
#stockfish --version && echo "✓ Stockfish installed"