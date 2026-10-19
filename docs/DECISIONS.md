# Decisions

## Project skeleton (2026-10-19)
- Flat `jobpilot/` package instead of `src/` layout: the src layout needs `pyproject.toml` + `pip install -e .`, which is overhead for an unpublished CLI.
- `requirements.txt` with an exact pin (`pytest==9.1.1`) instead of `pyproject.toml`: simpler while not packaging; the pin matches what was actually installed and tested.
- Logic in `main()`, called from `__main__.py`, instead of top-level code: tests can import and call it directly.
