# Decisions

## Project skeleton (2026-10-19)
- Flat `jobpilot/` package instead of `src/` layout: the src layout needs `pyproject.toml` + `pip install -e .`, which is overhead for an unpublished CLI.
- `requirements.txt` with an exact pin (`pytest==9.1.1`) instead of `pyproject.toml`: simpler while not packaging; the pin matches what was actually installed and tested.
- Logic in `main()`, called from `__main__.py`, instead of top-level code: tests can import and call it directly.

## extract subcommand (2026-10-19)
- Lookarounds `(?<!\w)…(?!\w)` instead of `\b`: `\b` can't match at a symbol edge, so "C++", "C#" and ".NET" would never be found.
- argparse instead of click/typer: built into Python, so no new dependency; enough for a few subcommands.
- JSON dictionary instead of YAML: `json` is built in (YAML needs PyYAML); bundled via `importlib.resources` so it loads from any folder.
- `extract_skills()` returns a list and never prints, instead of printing inside the matcher: unit tests need no output capture, and other commands can reuse it.
