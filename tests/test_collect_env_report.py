import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("collect_env_report", ROOT / "scripts" / "collect_env_report.py")
collect_env_report = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(collect_env_report)


def write_config(path: Path, body: str) -> Path:
    path.write_text(body.strip(), encoding="utf-8")
    return path


def test_path_report_does_not_expose_raw_path(tmp_path: Path) -> None:
    secret_path = tmp_path / "private-video-name.mp4"
    secret_path.write_bytes(b"media")
    report = collect_env_report.path_report(secret_path)
    assert report == {
        "configured": True,
        "placeholder": False,
        "exists": True,
        "kind": "file",
    }
    assert "private-video-name" not in str(report)


def test_build_report_redacts_paths_and_reports_key_presence(tmp_path: Path, monkeypatch) -> None:
    input_video = tmp_path / "sensitive_input_name.mp4"
    input_video.write_bytes(b"media")
    model_dir = tmp_path / "private_model_dir"
    model_dir.mkdir()
    config_path = write_config(
        tmp_path / "local.yaml",
        f"""
paths:
  input_video: "{input_video}"
  output_dir: "{tmp_path / 'outputs'}"
models:
  vibevoice_repo: "{model_dir}"
llm:
  api_key_env: "TEST_PRIVATE_KEY"
  model: "test-model"
  base_url: "https://example.invalid/v1"
tts:
  backend: "voxcpm"
  voxcpm_adapter: "my_adapter"
""",
    )
    monkeypatch.setenv("TEST_PRIVATE_KEY", "super-secret-value")
    monkeypatch.setattr(collect_env_report, "executable_report", lambda name: {"found": False})
    monkeypatch.setattr(collect_env_report, "torch_report", lambda: {"installed": False})

    report = collect_env_report.build_report(str(config_path))
    text = str(report)

    assert report["config_file"] == "local.yaml"
    assert report["llm"]["api_key_env"] == "TEST_PRIVATE_KEY"
    assert report["llm"]["api_key_set"] is True
    assert report["tts"]["backend"] == "voxcpm"
    assert report["tts"]["voxcpm_adapter_configured"] is True
    assert report["config_paths"]["paths.input_video"]["exists"] is True
    assert report["config_paths"]["models.vibevoice_repo"]["kind"] == "directory"
    assert "super-secret-value" not in text
    assert "sensitive_input_name" not in text
    assert "private_model_dir" not in text
    assert str(tmp_path) not in text


def test_placeholder_path_is_not_checked_for_existence() -> None:
    report = collect_env_report.path_report("/path/to/model")
    assert report["configured"] is True
    assert report["placeholder"] is True
    assert report["exists"] is False
