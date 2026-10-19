from pathlib import Path

import pytest

from jobpilot.extract import SkillsDict, extract_skills, load_skills

SKILLS: SkillsDict = {
    ".NET": ["dotnet"],
    "AWS": ["amazon web services"],
    "C#": ["csharp"],
    "C++": ["cpp"],
    "Docker": [],
    "GitHub Actions": [],
    "Java": [],
    "JavaScript": ["js"],
    "Kubernetes": ["k8s"],
    "Python": [],
    "SQL": [],
}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Strong PYTHON skills", ["Python"]),
        ("strong python skills", ["Python"]),
        ("Experience with JavaScript", ["JavaScript"]),
        ("Experience with JS", ["JavaScript"]),
        ("js, JavaScript and more js", ["JavaScript"]),
        ("Node.js backend", ["JavaScript"]),
        ("We write C++, C#. Also (C++)", ["C#", "C++"]),
        ("Built on .NET", [".NET"]),
        ("Docker/Kubernetes on (AWS)", ["AWS", "Docker", "Kubernetes"]),
        ("CI with GitHub\nActions", ["GitHub Actions"]),
        ("GitHub   Actions", ["GitHub Actions"]),
        ("Hosted on Amazon Web Services", ["AWS"]),
        ("k8s, sql, python", ["Kubernetes", "Python", "SQL"]),
    ],
)
def test_extract_matches(text: str, expected: list[str]) -> None:
    assert extract_skills(text, SKILLS) == expected


@pytest.mark.parametrize(
    ("text", "absent"),
    [
        ("JavaScript only", "Java"),
        ("NoSQL databases", "SQL"),
        ("Follow the laws", "AWS"),
        ("Pythonic code", "Python"),
        ("CCC", "C++"),
        ("aNET framework", ".NET"),
    ],
)
def test_no_match_inside_words_or_via_regex_metachars(text: str, absent: str) -> None:
    assert absent not in extract_skills(text, SKILLS)


@pytest.mark.parametrize("text", ["", "   \n\t  "])
def test_empty_text_finds_nothing(text: str) -> None:
    assert extract_skills(text, SKILLS) == []


def test_bundled_skills_load_and_compile() -> None:
    skills = load_skills()
    assert "Python" in skills
    # Searching compiles every skill's regex, so a bad entry would raise here.
    assert extract_skills("", skills) == []


def test_load_custom_skills_file(tmp_path: Path) -> None:
    path = tmp_path / "skills.json"
    path.write_text('{"Rust": ["rustlang"]}', encoding="utf-8")
    assert load_skills(path) == {"Rust": ["rustlang"]}


@pytest.mark.parametrize(
    "content",
    [
        "{not json",
        '["Python"]',
        '{"Python": "py"}',
        '{"Python": [1]}',
        '{"Python": [""]}',
        '{" ": []}',
    ],
)
def test_load_skills_rejects_bad_content(tmp_path: Path, content: str) -> None:
    path = tmp_path / "skills.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        load_skills(path)


def test_load_skills_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_skills(tmp_path / "missing.json")
