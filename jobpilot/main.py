import argparse
import sys
from pathlib import Path

from jobpilot.extract import canonicalize, extract_skills, load_skills, mentions
from jobpilot.llm import LLMError, llm_extract_skills


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jobpilot", description="Automate job-application prep.")
    subparsers = parser.add_subparsers(dest="command")

    extract = subparsers.add_parser("extract", help="List skills found in a job description.")
    extract.add_argument("jd_file", type=Path, help="Path to a job description text file.")
    extract.add_argument(
        "--skills",
        type=Path,
        default=None,
        help="Path to a skills JSON file (default: bundled skills.json).",
    )
    extract.add_argument(
        "--llm",
        action="store_true",
        help="Also ask Claude Haiku (via the claude CLI) and compare with the dictionary.",
    )
    return parser


def _fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def _print_section(title: str, lines: list[str]) -> None:
    print(f"{title} ({len(lines)}):")
    for line in lines or ["(none)"]:
        print(f"  {line}")


def _print_comparison(text: str, found: list[str], llm_found: list[str]) -> None:
    dict_set = set(found)
    llm_only = [skill for skill in llm_found if skill not in dict_set]
    # Dictionary hits are in the text by definition, so only LLM-only skills need checking.
    flagged = [
        skill if mentions(skill, text) else f"{skill}  [not in JD text — possible hallucination]"
        for skill in llm_only
    ]
    _print_section("Dictionary", found)
    _print_section("LLM", llm_found)
    _print_section("LLM-only", flagged)


def run_extract(jd_file: Path, skills_file: Path | None, use_llm: bool = False) -> int:
    try:
        text = jd_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return _fail(f"cannot read JD file {jd_file}: {e}")
    try:
        skills = load_skills(skills_file)
    except (OSError, ValueError) as e:
        return _fail(f"cannot load skills file: {e}")

    found = extract_skills(text, skills)
    if use_llm:
        try:
            llm_found = canonicalize(llm_extract_skills(text), skills)
        except LLMError as e:
            print(
                f"warning: LLM extraction failed ({e}); showing dictionary results only",
                file=sys.stderr,
            )
        else:
            _print_comparison(text, found, llm_found)
            return 0

    if not found:
        print("No skills found.")
    for skill in found:
        print(skill)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "extract":
        return run_extract(args.jd_file, args.skills, args.llm)
    parser.print_help()
    return 2
