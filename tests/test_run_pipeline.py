import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_pipeline", ROOT / "scripts" / "run_pipeline.py")
run_pipeline = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(run_pipeline)


def test_run_pipeline_dry_run_selects_stage_range(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_pipeline.py", "--config", "cfg.yaml", "--from-stage", "4", "--to-stage", "5", "--dry-run"],
    )
    assert run_pipeline.main() == 0
    output = capsys.readouterr().out
    assert "[4] verify:" in output
    assert "[5] generate-audio-chunks:" in output
    assert "[3] refine-translate:" not in output
    assert "[6] assemble:" not in output


def test_run_pipeline_skip_accepts_id_and_name(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_pipeline.py",
            "--config",
            "cfg.yaml",
            "--from-stage",
            "0",
            "--to-stage",
            "2",
            "--skip",
            "1",
            "--skip",
            "transcribe",
            "--dry-run",
        ],
    )
    assert run_pipeline.main() == 0
    output = capsys.readouterr().out
    assert "[0] extract-audio:" in output
    assert "[1] process-vocals: skipped" in output
    assert "[2] transcribe: skipped" in output


def test_run_pipeline_executes_commands_with_expected_config(monkeypatch) -> None:
    calls = []

    def fake_run(cmd, check):
        calls.append(cmd)

    monkeypatch.setattr(run_pipeline.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_pipeline.py", "--config", "cfg.yaml", "--from-stage", "1", "--to-stage", "2"],
    )
    assert run_pipeline.main() == 0
    assert calls[0][-1] == "cfg.yaml"
    assert calls[0][0] == "bash"
    assert calls[1][-2:] == ["--config", "cfg.yaml"]
