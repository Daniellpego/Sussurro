"""Entry point: `python -m sussurro`."""
from __future__ import annotations

import sys

from sussurro.app import run

if __name__ == "__main__":
    sys.exit(run())
