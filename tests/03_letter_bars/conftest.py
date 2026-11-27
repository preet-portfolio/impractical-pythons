"""Make the project's modules importable as plain ``letter_bars``."""

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2] / "projects" / "03_letter_bars"
sys.path.insert(0, str(PROJECT))
