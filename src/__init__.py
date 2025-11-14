"""Ensure the src package can be imported both as a module and as a script."""
from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.append(str(_SRC_DIR))
