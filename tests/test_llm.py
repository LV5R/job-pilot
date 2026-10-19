import json
import subprocess
from typing import Any

import pytest

from jobpilot.llm import LLMError, build_command, llm_extract_skills, parse_response


def envelope(result: str, is_error: bool = False) -> str:
    return json.dumps({"type": "result", "is_error": is_error, "result": result})


def fake_run(
    monkeypatch: pytest.MonkeyPatch,
    stdout: str = "",
    returncode: int = 0,
    stderr: str = "",
    raises: BaseException | None = None,
) -> list[dict[str, Any]]:
    """Replace subprocess.run; returns a list that records each call's arguments."""
    calls: list[dict[str, Any]] = []

    def run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"cmd": cmd, **kwargs})
        if raises is not None:
            raise raises
        return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)

    monkeypatch.setattr("jobpilot.llm.subprocess.run", run)
    return calls


def test_build_command_flags() -> None:
    cmd = build_command()
    assert cmd[:2] == ["claude", "-p"]
    assert cmd[cmd.index("--model") + 1] == "haiku"
    assert cmd[cmd.index("--output-format") + 1] == "json"
    assert cmd[cmd.index("--tools") + 1] == ""
    assert "--no-session-persistence" in cmd


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        ('["Python", "AWS"]', ["AWS", "Python"]),
        ('```json\n["Python"]\n```', ["Python"]),
        ('```\n["Python"]\n```', ["Python"]),
        ('["Python", "python", " Python ", ""]', ["Python"]),
        ("[]", []),
    ],
)
def test_parse_response_valid(result: str, expected: list[str]) -> None:
    assert parse_response(envelope(result)) == expected


@pytest.mark.parametrize(
    "stdout",
    [
        "not json",
        '["Python"]',
        json.dumps({"is_error": False}),
        envelope("rate limited", is_error=True),
        envelope("Here are the skills: Python"),
        envelope('{"skills": ["Python"]}'),
        envelope('["Python", 3]'),
    ],
)
def test_parse_response_rejects_bad_output(stdout: str) -> None:
    with pytest.raises(LLMError):
        parse_response(stdout)


def test_llm_extract_sends_jd_on_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = fake_run(monkeypatch, stdout=envelope('["Python"]'))
    assert llm_extract_skills("Need Python devs", timeout=5) == ["Python"]
    (call,) = calls
    assert call["cmd"] == build_command()
    assert "Need Python devs" in call["input"]
    assert call["timeout"] == 5
    assert call["capture_output"] and call["text"]


@pytest.mark.parametrize(
    ("raises", "reason"),
    [
        (FileNotFoundError("claude"), "not found"),
        (PermissionError("denied"), "cannot run"),
        (subprocess.TimeoutExpired("claude", 60), "timed out"),
    ],
)
def test_llm_extract_run_failures(
    monkeypatch: pytest.MonkeyPatch, raises: BaseException, reason: str
) -> None:
    fake_run(monkeypatch, raises=raises)
    with pytest.raises(LLMError, match=reason):
        llm_extract_skills("text")


def test_llm_extract_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_run(monkeypatch, returncode=1, stderr="Invalid API key\n")
    with pytest.raises(LLMError, match="code 1: Invalid API key"):
        llm_extract_skills("text")
