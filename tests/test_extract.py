from pathlib import Path

import pytest

from jobpilot.extract import SkillsDict, canonicalize, extract_skills, load_skills, mentions

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


GRADUATE_JD_EXCERPT = """
•	Software development using languages such as Python, Java, C++, JavaScript or similar technologies.
•	Data structures, algorithms and problem-solving skills to design scalable and efficient solutions.
•	Application development across web, mobile, API and enterprise platforms.
•	Database design, SQL and data management concepts.
•	Cloud technologies and modern engineering practices, including Azure, containerisation, automation and DevOps principles.
•	Cybersecurity fundamentals, including secure coding, networking concepts, identity management and threat awareness.
•	Agile ways of working, software testing, quality engineering and continuous improvement practices.
"""


def test_bundled_skills_on_graduate_jd_excerpt() -> None:
    # Regression guard: a real JD's bullets, so dictionary edits can't silently drop hits.
    assert extract_skills(GRADUATE_JD_EXCERPT, load_skills()) == [
        "Agile",
        "API",
        "Azure",
        "C++",
        "Containers",
        "Cybersecurity",
        "Data Structures & Algorithms",
        "DevOps",
        "Java",
        "JavaScript",
        "Python",
        "Software Testing",
        "SQL",
    ]


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


@pytest.mark.parametrize(
    ("term", "text", "expected"),
    [
        ("Python", "Strong python skills", True),
        ("C++", "We use C++ daily", True),
        (".NET", "Built on .NET", True),
        ("GitHub Actions", "GitHub\nActions", True),
        ("Python", "Pythonic code", False),
        ("Java", "JavaScript only", False),
        ("Terraform", "Python and AWS", False),
        ("  ", "anything", False),
    ],
)
def test_mentions(term: str, text: str, expected: bool) -> None:
    assert mentions(term, text) is expected


def test_canonicalize_maps_synonyms_and_keeps_unknown() -> None:
    names = ["amazon web services", "k8s", "PYTHON", "Terraform", "AWS"]
    assert canonicalize(names, SKILLS) == ["AWS", "Kubernetes", "Python", "Terraform"]
