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
