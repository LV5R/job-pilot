import pytest

from jobpilot.main import main


def test_main_prints_ready(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    assert capsys.readouterr().out == "jobpilot ready\n"
