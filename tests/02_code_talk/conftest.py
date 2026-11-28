"""Make the project's modules importable as plain ``code_talk``."""

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2] / "projects" / "02_code_talk"
sys.path.insert(0, str(PROJECT))
