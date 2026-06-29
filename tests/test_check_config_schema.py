from __future__ import annotations

import check_config_schema


def test_schema_cli_returns_zero_for_valid_config(monkeypatch, capsys) -> None:
    monkeypatch.setattr(check_config_schema, "parse_args", lambda: type("Args", (), {"config": "config.yaml", "json": False, "no_summary": False})())
    monkeypatch.setattr(check_config_schema, "load_config", lambda path: {
        "paths": {
            "input_video": "input.mp4",
            "input_wav": "input.wav",
            "output_dir": "outputs",
            "vocal_source_for_asr": "outputs/vocals.wav",
            "instrumental_audio": "outputs/instrumental.wav",
            "asr_json": "outputs/asr.json",
            "refined_json": "outputs/refined.json",
            "dub_chunk_dir": "outputs/chunks",
            "temp_mixed_wav": "outputs/temp.wav",
            "final_video": "outputs/final.mp4",
        },
        "models": {
            "audio_separator_model": "Kim_Vocal_2.onnx",
            "audio_separator_model_dir": "models/separator",
            "vibevoice_repo": "repos/VibeVoice",
            "vibevoice_asr_path": "models/VibeVoice-ASR",
            "qwen_asr_path": "models/Qwen3-ASR",
        },
        "llm": {"api_base": "https://example.invalid", "model": "demo"},
        "tts": {"backend": "manual"},
    })

    assert check_config_schema.main() == 0
    assert "ERROR=0" in capsys.readouterr().out


def test_schema_cli_returns_one_for_invalid_config(monkeypatch, capsys) -> None:
    monkeypatch.setattr(check_config_schema, "parse_args", lambda: type("Args", (), {"config": "config.yaml", "json": False, "no_summary": False})())
    monkeypatch.setattr(check_config_schema, "load_config", lambda path: {"tts": {"backend": "bad"}})

    assert check_config_schema.main() == 1
    rendered = capsys.readouterr().out
    assert "[ERROR]" in rendered
    assert "tts.backend" in rendered


def test_schema_cli_json_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(check_config_schema, "parse_args", lambda: type("Args", (), {"config": "config.yaml", "json": True, "no_summary": False})())
    monkeypatch.setattr(check_config_schema, "load_config", lambda path: {"tts": {"backend": "bad"}})

    assert check_config_schema.main() == 1
    rendered = capsys.readouterr().out
    assert '"summary"' in rendered
    assert '"issues"' in rendered
