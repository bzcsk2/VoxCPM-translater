from pathlib import Path

import pytest

from runtime_checks import ensure_parent_dir, require_choice, require_dir, require_file, require_positive_float


def test_require_file_returns_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "input.txt"
    path.write_text("ok", encoding="utf-8")

    assert require_file(path, "input") == path


def test_require_file_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        require_file(tmp_path / "missing.txt", "input")


def test_require_dir_returns_existing_directory(tmp_path: Path) -> None:
    assert require_dir(tmp_path, "directory") == tmp_path


def test_ensure_parent_dir_creates_parent(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "out.wav"

    assert ensure_parent_dir(output, "output") == output
    assert output.parent.exists()


def test_require_choice_validates_allowed_values() -> None:
    assert require_choice("warn", "policy", {"error", "warn", "skip"}) == "warn"
    with pytest.raises(ValueError):
        require_choice("bad", "policy", {"error", "warn", "skip"})


def test_require_positive_float_parses_values() -> None:
    assert require_positive_float("0.7", "ratio") == 0.7
    with pytest.raises(ValueError):
        require_positive_float("0", "ratio")
