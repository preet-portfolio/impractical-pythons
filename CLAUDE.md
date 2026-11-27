# Impractical Pythons

A playground of original, creative, fun Python projects, inspired by the ideas in
*Impractical Python Projects* (word games, cryptography, statistics, simulation,
genetic algorithms, astronomy...), but **not** copies of the book's chapters.
Each project should feel like its own idea, with real-world flavour where possible.

## Where it lives

- **Web-first and interactive.** Every project must be playable by visitors in the
  browser, not just runnable in a terminal.
- **One gallery site** on Vercel (project `impractical-pythons`, team
  `preetportfolios-projects`, root directory `web/`), with a page per project.
- **Public GitHub repo** `preet-portfolio/impractical-pythons`. Public means no
  personal data, keys or private details in code, copy or commits.
- **Listed on the portfolio.** The main site is `preet-portfolio.github.io` (Next.js
  static export on GitHub Pages, local copy at `../preet-portfolio.github.io`). Once
  the gallery is live, add one entry to its `src/data/work.json` under
  `"group": "projects"` (fields: id, name, line, status, kind, links: "Open ..." +
  "Source"), following that repo's own CLAUDE.md. Never list it before it's live.
- **Own design, not a copy of `../tiny-python-tested`.** The user wants this site to
  be its own thing; don't borrow that project's setup or look.
- **Every project is its own stall, with its own look.** The gallery is a seaside pier;
  each project page gets a distinct palette, typefaces and centrepiece (Alias Slots is a
  fruit machine, Code-Talk a spy's case file, Letter Bars a seaside rock shop, Mirror
  Spells a Hall of Mirrors). Never
  reuse a previous project's design; the gallery card borrows the stall's look too.
- **Fun first, for portfolio visitors.** Page copy is playful and plain, with no code words
  above the fold; the Python detail lives in the README and a "Peek at the Python" link.
  Every page and the gallery credit *Impractical Python Projects* by Lee Vaughan with a
  link to the book. Check each page against `docs/ux-research.md` (proto-personas and
  checklist) before calling it done.

## How Python runs on the web

- **Pyodide (CPython in WebAssembly) in the visitor's browser.** No backend, no API
  routes; the site is static. The exact same Python modules in `projects/` are loaded
  by the web page, so tests cover what visitors run.
- **Web stack:** Vite + TypeScript, no framework, one HTML page per project
  (`web/<slug>/index.html`, registered in `web/vite.config.ts` inputs and listed in
  `web/src/projects.ts` for the gallery home).
- **How the Python gets in:** `web/src/py/sources.ts` imports a project's `.py` files
  as text with `import.meta.glob(..., { query: "?raw" })` (no copy step). The module
  worker `web/src/py/worker.ts` loads Pyodide from jsDelivr (pinned
  `PYODIDE_VERSION`, currently Python 3.14), writes the files into Pyodide's
  filesystem and calls them through one `_bridge` function that returns JSON.
  `web/src/py/python.ts` wraps the worker in promises:
  `python.init(project, files, BRIDGE)` then `python.call(fn, args)`.
- **Adding a project page:** add a glob to `sources.ts` (options written inline: Vite
  needs literals), write the page's own `BRIDGE` (a small Python string defining
  `_bridge(fn, args_json)`) in `web/src/<slug>-page.ts`, give the page its own stylesheet
  `web/src/<slug>.css` scoped under a body class (`body.talk`, `body.rock`) so stalls
  don't leak into each other, and add the input to `vite.config.ts` and the card to
  `projects.ts`. Pyodide keeps each project under `/home/pyodide/projects/<project>`.
  If the dev server was running when a new `projects/NN_*` folder appeared, touch
  `sources.ts` so Vite re-runs the glob.
- Project logic must be **pure, importable functions** (no `input()`/`print` loops in
  the core). `main.py` is a thin CLI wrapper; the web page calls the same functions.
- Only use packages Pyodide ships (stdlib, numpy, matplotlib, pillow, etc. — check the
  Pyodide package list before adding one). Pyodide's Python can lag the local one
  (local is 3.15), so avoid brand-new syntax/stdlib features.
- Heavy work runs in a Web Worker so the page stays responsive.

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
web/                      # Next.js static-export gallery (added with the first project)
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
- Lint/format: `uv run ruff check .` and `uv run ruff format .` (docstrings follow
  PEP 257, Google style; ruff enforces it outside `tests/`)
- Web: `cd web && npm install`, then `npm run dev` (http://localhost:5180) or
  `npm run build` (type-checks, outputs `web/dist`). The browser pane can start the
  dev server from `.claude/launch.json` ("web").
- Tests import a project's modules by adding its folder to `sys.path` in a
  per-project `tests/NN_name/conftest.py` (folders start with digits, so they can't
  be packages). Give test files unique names (`test_<project>.py`).

## Conventions

- Type hints on function signatures; `from __future__ import annotations` not needed.
- Use `pathlib` for files, `argparse` for CLI options, `random.Random(seed)` when
  results should be reproducible.
- Guard entry points with `if __name__ == "__main__":`.
- Write tests for the core logic (pure functions), not for printing/UI.
- Large downloaded datasets go in `data/` and are git-ignored if over ~5 MB;
  the README says where to get them.
- Before calling a project done: it runs, `pytest` passes, `ruff check` is clean,
  `npm run build` in `web/` passes, and it works in the browser.

## Git

- Imperative commit subjects with a body that says why. One change per commit.
- Branch, open a PR, merge to `main`; Vercel deploys `main`.
