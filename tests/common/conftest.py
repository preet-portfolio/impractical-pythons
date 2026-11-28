"""Make the shared modules importable as plain ``wordlist`` and ``decency``."""

import sys
from pathlib import Path

COMMON = Path(__file__).resolve().parents[2] / "projects" / "common"
sys.path.insert(0, str(COMMON))
