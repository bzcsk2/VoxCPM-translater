import json
from pathlib import Path

import diagnose
from config_checks import CheckResult


def test_collect_stage_reports_uses_stage_status_and_manifest(monkeypatch, tmp_path: Path) -> None:
    cfg = {"paths": {"output_dir": str(tmp_path / "outputs")}}

    monkeypatch.setattr(diagnose, "STAGES", [(0, "extract-audio", []), (1, "process-vocals", [])])
    monkeypatch.setattr(diagnose, "stage_status", lambda stage_id, cfg: ("complete", f"stage {stage_id}"))
    monkeypatch.setattr(diagnose, "read_stage_manifest", lambda stage_id, name, cfg: {"status": "success"} if stage_id == 0 else None)
    monkeypatch.setattr(diagnose, "format_manifest_summary", lambda manifest: "last_run=success")

    reports = diagnose.collect_stage_reports(cfg, 0, 1)

    assert len(reports) == 2
    assert reports[0].status == "complete"
    assert reports[0].last_run == "last_run=success"
    assert reports[1].last_run is None


def test_collect_report_handles_config_load_error(monkeypatch) -> None:
    monkeypatch.setattr(diagnose, "load_config", lambda path: (_ for _ in ()).throw(RuntimeError("bad config")))

    report = diagnose.collect_report("missing.yaml", 0, 8, include_artifacts=False)

    assert report["config"]["loaded"] is False
    assert "bad config" in report["config"]["error"]
    assert report["environment"] is None


def test_collect_report_includes_environment_and_stage_status(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(diagnose, "load_config", lambda path: {"paths": {"output_dir": str(tmp_path)}})
    monkeypatch.setattr(diagnose, "run_environment_checks", lambda cfg: [CheckResult("OK", "ffmpeg", "found ffmpeg")])
    monkeypatch.setattr(diagnose, "collect_stage_reports", lambda cfg, start, end: [diagnose.StageReport(0, "extract-audio", "missing", "input.wav")])
    monkeypatch.setattr(diagnose, "_safe_run", lambda command: diagnose.CommandReport(command[0], True, "ok"))
    monkeypatch.setattr(diagnose, "_git_head", lambda: "abc123")

    report = diagnose.collect_report("config.yaml", 0, 0, include_artifacts=False)

    assert report["config"]["loaded"] is True
    assert report["environment"]["summary"]["OK"] == 1
    assert report["stages"][0]["name"] == "extract-audio"


def test_collect_artifact_issues_skips_missing_files(tmp_path: Path) -> None:
    cfg = {
        "paths": {
            "asr_json": str(tmp_path / "asr.json"),
            "refined_json": str(tmp_path / "refined.json"),
        }
    }

    issues, skipped = diagnose.collect_artifact_issues(cfg)

    assert issues == []
    assert skipped == "ASR or refined JSON file is not available yet"


def test_collect_artifact_issues_validates_alignment_and_chunks(tmp_path: Path) -> None:
    asr_json = tmp_path / "asr.json"
    refined_json = tmp_path / "refined.json"
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    asr = [{"id": 0, "start": "00:00:00.000", "end": "00:00:01.000", "speaker": "spk1", "text_zh": "你好"}]
    refined = [{**asr[0], "zh_fixed": "你好。", "en": "Hello."}]
    asr_json.write_text(json.dumps(asr), encoding="utf-8")
    refined_json.write_text(json.dumps(refined), encoding="utf-8")

    issues, skipped = diagnose.collect_artifact_issues(
        {
            "paths": {
                "asr_json": str(asr_json),
                "refined_json": str(refined_json),
                "dub_chunk_dir": str(chunk_dir),
            }
        }
    )

    assert skipped is None
    assert any(issue.path == "tts_chunks" for issue in issues)


def test_render_markdown_includes_key_sections() -> None:
    report = {
        "config": {"path": "configs/local.yaml", "loaded": True, "error": None},
        "system": {"python": "3.10", "platform": "linux", "git_head": "abc123"},
        "commands": [{"command": "ffmpeg", "available": True, "output": "ffmpeg version"}],
        "environment": {"summary": {"OK": 1, "WARN": 0, "FAIL": 0}, "results": [{"level": "OK", "name": "ffmpeg", "message": "found"}]},
        "stages": [{"stage_id": 0, "name": "extract-audio", "status": "missing", "detail": "input.wav", "last_run": None}],
        "artifacts": {"skipped_reason": "not ready", "summary": {"ERROR": 0, "WARN": 0, "INFO": 0}, "issues": []},
    }

    rendered = diagnose.render_markdown(report)

    assert "# VoxCPM Translator diagnostic report" in rendered
    assert "## Environment checks" in rendered
    assert "## Stage status" in rendered
    assert "Artifact validation" in rendered
