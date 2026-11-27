"""Make the project's modules importable by plain name."""

import sys
from pathlib import Path

PROJECTS = Path(__file__).resolve().parents[2] / "projects"
sys.path.insert(0, str(PROJECTS / "06_pier_telegraph"))
