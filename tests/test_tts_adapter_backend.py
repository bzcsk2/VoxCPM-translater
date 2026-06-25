import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generate_audio_chunks", ROOT / "scripts" / "05_generate_audio_chunks.py")
generate_audio_chunks = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(generate_audio_chunks)


def test_run_voxcpm_adapter_calls_configured_module(tmp_path: Path, monkeypatch) -> None:
    calls = []
    module = types.ModuleType("fake_voxcpm_adapter")

    def generate_audio(segment, output_path, config):
        calls.append((segment, output_path, config))
        output_path.write_bytes(b"fake wav bytes")

    module.generate_audio = generate_audio
    monkeypatch.setitem(sys.modules, "fake_voxcpm_adapter", module)

    segments = [
        {"id": 0, "speaker": "A", "en": "Hello."},
        {"id": 1, "speaker": "B", "en": "[Music]"},
    ]
    cfg = {
        "tts": {
            "voxcpm_adapter": "fake_voxcpm_adapter",
            "voxcpm_adapter_function": "generate_audio",
        }
    }
    generate_audio_chunks.run_voxcpm_adapter(segments, tmp_path, cfg, overwrite=False)

    assert len(calls) == 1
    assert calls[0][0]["id"] == 0
    assert (tmp_path / "raw_0.wav").exists()
    assert not (tmp_path / "raw_1.wav").exists()


def test_run_voxcpm_adapter_requires_module(tmp_path: Path) -> None:
    try:
        generate_audio_chunks.run_voxcpm_adapter([], tmp_path, {"tts": {}}, overwrite=False)
    except RuntimeError as exc:
        assert "voxcpm_adapter" in str(exc)
    else:
        raise AssertionError("expected missing adapter configuration to fail")


def test_run_python_adapter_detects_missing_output(tmp_path: Path, monkeypatch) -> None:
    module = types.ModuleType("silent_adapter")

    def generate_audio(segment, output_path, config):
        return None

    module.generate_audio = generate_audio
    monkeypatch.setitem(sys.modules, "silent_adapter", module)

    try:
        generate_audio_chunks.run_python_adapter(
            [{"id": 0, "en": "Hello."}],
            tmp_path,
            {},
            "silent_adapter",
            "generate_audio",
            overwrite=False,
        )
    except FileNotFoundError as exc:
        assert "raw_0.wav" in str(exc)
    else:
        raise AssertionError("expected missing adapter output to fail")
