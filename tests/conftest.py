from typing import Any

import pytest


@pytest.fixture(autouse=True)
def block_real_claude(monkeypatch: pytest.MonkeyPatch) -> None:
    # Safety net: tests must never call the real claude CLI. Tests that need
    # subprocess.run install their own fake, which replaces this one.
    def blocked(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("real subprocess call in tests; mock subprocess.run")

    monkeypatch.setattr("jobpilot.llm.subprocess.run", blocked)
