"""Make the project's modules importable as plain ``slots`` / ``themes`` / ``main``.

Project folders start with a number, so they can't be imported as packages.
The browser does the same thing: it puts these files on Pyodide's sys.path.
"""

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2] / "projects" / "01_alias_slots"
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "style_clinic"))
