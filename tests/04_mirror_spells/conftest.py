"""Make the project's modules importable as plain ``mirror`` and ``wordlist``."""

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2] / "projects" / "04_mirror_spells"
sys.path.insert(0, str(PROJECT))
