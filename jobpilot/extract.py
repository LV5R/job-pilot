import json
import re
from importlib.resources import files
from pathlib import Path

SkillsDict = dict[str, list[str]]


def load_skills(path: Path | None = None) -> SkillsDict:
    """Load a skill -> synonyms mapping; defaults to the bundled skills.json."""
    if path is None:
        raw = files("jobpilot").joinpath("data/skills.json").read_text(encoding="utf-8")
    else:
        raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON: {e}") from e
    return _validate(data)


def _validate(data: object) -> SkillsDict:
    if not isinstance(data, dict):
        raise ValueError("skills file must be a JSON object of skill -> list of synonyms")
    for skill, synonyms in data.items():
        if not skill.strip():
            raise ValueError("skill names must be non-empty")
        if not isinstance(synonyms, list) or not all(
            isinstance(s, str) and s.strip() for s in synonyms
        ):
            raise ValueError(f"synonyms for {skill!r} must be a list of non-empty strings")
    return data


def _term_pattern(term: str) -> str:
    # Escape regex metacharacters (C++, .NET) and let any whitespace run
    # separate words, so "GitHub Actions" also matches across a line break.
    return r"\s+".join(re.escape(word) for word in term.split())


def _skill_regex(skill: str, synonyms: list[str]) -> re.Pattern[str]:
    terms = sorted({skill, *synonyms}, key=len, reverse=True)
    alternation = "|".join(_term_pattern(t) for t in terms)
    # Lookarounds instead of \b: \b needs a word character on one side, so it
    # never matches after the "+" in "C++" or before the "." in ".NET".
    return re.compile(rf"(?<!\w)(?:{alternation})(?!\w)", re.IGNORECASE)


def extract_skills(text: str, skills: SkillsDict) -> list[str]:
    """Return the skills mentioned in text, each once, sorted case-insensitively."""
    found = [
        skill
        for skill, synonyms in skills.items()
        if _skill_regex(skill, synonyms).search(text)
    ]
    return sorted(found, key=str.casefold)
