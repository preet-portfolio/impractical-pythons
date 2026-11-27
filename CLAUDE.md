# Impractical Pythons

A playground of original, creative, fun Python projects, inspired by the ideas in
*Impractical Python Projects* (word games, cryptography, statistics, simulation,
genetic algorithms, astronomy...), but **not** copies of the book's chapters.
Each project should feel like its own idea, with real-world flavour where possible.

## How we work

- **Claude builds, then explains.** Claude writes the full project, then walks the
  user through it: the approach, the new Python concepts/modules/built-ins used,
  and why they were chosen.
- Every project's explanation ends with a short **"What's new here"** list
  (modules, techniques, tricks) and 2–3 **"Try this next"** ideas the user could
  hack on themselves.
- Before building a new project, agree on the idea and a rough design in a few
  lines. Keep the first version small and runnable, then extend.
- Favour clarity over cleverness: readable names, small functions, docstrings
  explaining *why*. This is a learning repo.

## Repo layout

```
projects/
  NN_short_name/          # one folder per project, numbered in build order
    README.md             # the idea, how to run it, what it teaches
    main.py               # entry point (python -m or uv run)
    *.py                  # supporting modules
    data/                 # small input files (word lists, datasets), if any
tests/
  NN_short_name/          # pytest tests per project, mirroring projects/
PROJECTS.md               # index of all projects with one-line summaries
```

- Folder names: `NN_snake_case` (e.g. `01_palindrome_hunter`). Number in build order.
- Each project is self-contained; shared helpers only go in `projects/common/`
  once two projects genuinely need the same code.
- When a project is added or renamed, update `PROJECTS.md`.

## Tooling

- Python 3.13+ (machine has 3.15), managed with **uv**.
- Dependencies live in the root `pyproject.toml`. Add with `uv add <pkg>`
  (dev tools: `uv add --dev <pkg>`). Prefer the standard library; reach for
  third-party packages (matplotlib, numpy, pillow, etc.) when they make the
  project more fun or teach something worthwhile.
- Run a project: `uv run python projects/NN_name/main.py`
- Tests: `uv run pytest` (or `uv run pytest tests/NN_name`)
- Lint/format: `uv run ruff check .` and `uv run ruff format .`

## Conventions

- Type hints on function signatures; `from __future__ import annotations` not needed.
- Use `pathlib` for files, `argparse` for CLI options, `random.Random(seed)` when
  results should be reproducible.
- Guard entry points with `if __name__ == "__main__":`.
- Write tests for the core logic (pure functions), not for printing/UI.
- Large downloaded datasets go in `data/` and are git-ignored if over ~5 MB;
  the README says where to get them.
- Before calling a project done: it runs, `pytest` passes, `ruff check` is clean.
