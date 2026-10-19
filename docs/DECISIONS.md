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

## Dictionary: concept skills (2026-10-19)
- Concept skills (Agile, DevOps, Cybersecurity…) added alongside tools, instead of tools only: graduate JDs name areas more often than tools, and recruiters filter on these terms.
- A concept matches only on specific phrases ("software testing", "quality engineering"), never a bare generic word like "testing"; Networking excluded because "networking opportunities" would be a false positive.
- Real-JD excerpt kept as a regression test instead of relying only on synthetic cases: catches dictionary edits that silently drop hits.

## extract --llm (2026-10-19)
- `claude -p` via subprocess instead of the `anthropic` SDK: reuses the existing Claude Code login and adds no dependency; cost is CLI startup time.
- `--tools ""` and the JD sent on stdin: a JD is untrusted text, so a prompt injection has no tools to use; stdin avoids argv length limits and JD lines parsed as flags.
- LLM-only skills missing from the JD text are flagged, not hidden: the model may correctly normalise wording ("problem-solving"), so the user decides.
- Any LLM failure (missing CLI, 60 s timeout, bad output) falls back to dictionary-only with a stderr warning and exit 0, instead of failing the command.
