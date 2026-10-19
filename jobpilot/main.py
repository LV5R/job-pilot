import argparse
import sys
from pathlib import Path

from jobpilot.extract import extract_skills, load_skills


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
    return parser


def _fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def run_extract(jd_file: Path, skills_file: Path | None) -> int:
    try:
        text = jd_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return _fail(f"cannot read JD file {jd_file}: {e}")
    try:
        skills = load_skills(skills_file)
    except (OSError, ValueError) as e:
        return _fail(f"cannot load skills file: {e}")

    found = extract_skills(text, skills)
    if not found:
        print("No skills found.")
    for skill in found:
        print(skill)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "extract":
        return run_extract(args.jd_file, args.skills)
    parser.print_help()
    return 2
