import subprocess
from pathlib import Path

import pytest

from jobpilot.main import main


def write_jd(tmp_path: Path, text: str) -> str:
    path = tmp_path / "jd.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_extract_prints_sorted_skills(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    jd = write_jd(tmp_path, "Python, Docker and AWS required. Bash is a plus.")
    assert main(["extract", jd]) == 0
    assert capsys.readouterr().out == "AWS\nBash\nDocker\nPython\n"


def test_extract_no_skills(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    jd = write_jd(tmp_path, "Looking for a friendly barista.")
    assert main(["extract", jd]) == 0
    assert capsys.readouterr().out == "No skills found.\n"


def test_extract_custom_skills_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    skills = tmp_path / "skills.json"
    skills.write_text('{"Rust": []}', encoding="utf-8")
    jd = write_jd(tmp_path, "Rust and Python")
    assert main(["extract", jd, "--skills", str(skills)]) == 0
    assert capsys.readouterr().out == "Rust\n"


def test_extract_missing_jd_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["extract", str(tmp_path / "missing.txt")]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "cannot read JD file" in captured.err


def test_extract_non_utf8_jd_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    jd = tmp_path / "jd.txt"
    jd.write_bytes(b"\xff\xfe\x00bad")
    assert main(["extract", str(jd)]) == 1
    assert "cannot read JD file" in capsys.readouterr().err


def test_extract_malformed_skills_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    skills = tmp_path / "skills.json"
    skills.write_text("{bad", encoding="utf-8")
    jd = write_jd(tmp_path, "Python")
    assert main(["extract", jd, "--skills", str(skills)]) == 1
    assert "cannot load skills file" in capsys.readouterr().err


def test_extract_requires_jd_argument() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["extract"])
    assert exc.value.code == 2


def test_no_subcommand_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "usage: jobpilot" in capsys.readouterr().out


def test_extract_llm_compares_and_flags_hallucinations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    jd = write_jd(tmp_path, "Python and Amazon Web Services required. Terraform is a plus.")
    # LLM says "Amazon Web Services" (dictionary synonym -> AWS), finds Terraform
    # (in text, not in dictionary) and invents Rust (not in text).
    monkeypatch.setattr(
        "jobpilot.main.llm_extract_skills",
        lambda text: ["Amazon Web Services", "Python", "Rust", "Terraform"],
    )
    assert main(["extract", jd, "--llm"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == (
        "Dictionary (2):\n"
        "  AWS\n"
        "  Python\n"
        "LLM (4):\n"
        "  AWS\n"
        "  Python\n"
        "  Rust\n"
        "  Terraform\n"
        "LLM-only (2):\n"
        "  Rust  [not in JD text — possible hallucination]\n"
        "  Terraform\n"
    )


def test_extract_llm_failure_falls_back_to_dictionary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    jd = write_jd(tmp_path, "Python and Docker required.")
    def timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired("claude", 60)

    # Patch at the subprocess level so the real error-mapping in llm.py runs too.
    monkeypatch.setattr("jobpilot.llm.subprocess.run", timeout)
    assert main(["extract", jd, "--llm"]) == 0
    captured = capsys.readouterr()
    assert captured.out == "Docker\nPython\n"
    assert "LLM extraction failed (timed out after 60s)" in captured.err
