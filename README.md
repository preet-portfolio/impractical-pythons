# Impractical Pythons 🐍

Original, creative and (mostly) impractical Python projects, inspired by
*Impractical Python Projects*. Each project lives in `projects/` and teaches
something new along the way.

See [PROJECTS.md](PROJECTS.md) for the list.

## Setup

```bash
uv sync
uv run pytest
```

Play a project in the terminal:

```bash
uv run python projects/01_alias_slots/main.py
```

Run the web gallery locally (Python runs in the browser via Pyodide):

```bash
cd web && npm install && npm run dev
```
