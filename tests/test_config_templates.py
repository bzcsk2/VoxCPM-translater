from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs"
REQUIRED_TOP_LEVEL_KEYS = {
    "paths",
    "models",
    "llm",
    "runtime",
    "audio_extract",
    "vocal_extraction",
    "asr",
    "tts",
    "assembly",
    "subtitles",
}
REQUIRED_PATH_KEYS = {
    "input_video",
    "input_wav",
    "output_dir",
    "vocal_source_for_asr",
    "instrumental_audio",
    "asr_json",
    "refined_json",
    "dub_chunk_dir",
    "temp_mixed_wav",
    "final_video",
}
REQUIRED_MODEL_KEYS = {
    "audio_separator_model",
    "audio_separator_model_dir",
    "vibevoice_repo",
    "vibevoice_asr_path",
    "qwen_asr_path",
    "voxcpm_model_path",
    "latentsync_dir",
}


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path} must parse as a mapping"
    return data


def test_committed_config_templates_are_parseable() -> None:
    for name in ["default.yaml", "local.example.yaml", "ci.yaml"]:
        data = _load_yaml(CONFIG_DIR / name)
        assert REQUIRED_TOP_LEVEL_KEYS <= set(data), name


def test_config_templates_keep_required_paths_and_models() -> None:
    for name in ["default.yaml", "local.example.yaml", "ci.yaml"]:
        data = _load_yaml(CONFIG_DIR / name)
        assert REQUIRED_PATH_KEYS <= set(data["paths"]), name
        assert REQUIRED_MODEL_KEYS <= set(data["models"]), name


def test_local_example_is_not_identical_to_default() -> None:
    default_data = _load_yaml(CONFIG_DIR / "default.yaml")
    local_data = _load_yaml(CONFIG_DIR / "local.example.yaml")

    assert local_data["paths"]["input_video"] != default_data["paths"]["input_video"]
    assert local_data["models"]["audio_separator_model_dir"] != default_data["models"]["audio_separator_model_dir"]


def test_ci_config_uses_test_output_paths() -> None:
    ci_data = _load_yaml(CONFIG_DIR / "ci.yaml")

    assert ci_data["paths"]["output_dir"] == "test_output"
    assert ci_data["runtime"]["asr_device"] == "cpu"
    assert ci_data["tts"]["backend"] == "manual"
