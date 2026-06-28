import importlib.util
import json
import math
import shutil
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(module_name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write_silence_wav(path: Path, duration_ms: int, sample_rate: int = 8000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = math.ceil(sample_rate * duration_ms / 1000)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * frame_count)


def test_manual_tts_and_assembly_smoke(tmp_path: Path, monkeypatch) -> None:
    refined_json = tmp_path / "refined.json"
    chunk_dir = tmp_path / "chunks"
    bgm_wav = tmp_path / "bgm.wav"
    temp_wav = tmp_path / "mixed.wav"
    output_video = tmp_path / "final.mp4"
    input_video = tmp_path / "input.mp4"

    refined_json.write_text(
        json.dumps(
            [
                {
                    "id": 0,
                    "start": "00:00:00.000",
                    "end": "00:00:00.500",
                    "speaker": "A",
                    "text_zh": "你好",
                    "zh_fixed": "你好。",
                    "en": "Hello.",
                },
                {
                    "id": 1,
                    "start": "00:00:00.500",
                    "end": "00:00:01.000",
                    "speaker": "B",
                    "text_zh": "[Music]",
                    "zh_fixed": "[Music]",
                    "en": "[Music]",
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    write_silence_wav(bgm_wav, duration_ms=1000)
    write_silence_wav(chunk_dir / "raw_0.wav", duration_ms=500)
    input_video.write_bytes(b"placeholder video")

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"""
paths:
  refined_json: "{refined_json}"
  dub_chunk_dir: "{chunk_dir}"
  instrumental_audio: "{bgm_wav}"
  temp_mixed_wav: "{temp_wav}"
  input_video: "{input_video}"
  final_video: "{output_video}"
tts:
  backend: "manual"
assembly:
  min_speed_ratio: 0.70
  audio_bitrate: "192k"
  missing_chunk_policy: "error"
""".strip(),
        encoding="utf-8",
    )

    tts_stage = load_script("generate_audio_chunks", "scripts/05_generate_audio_chunks.py")
    monkeypatch.setattr(sys, "argv", ["05_generate_audio_chunks.py", "--config", str(config_path)])
    assert tts_stage.main() == 0

    assemble_stage = load_script("assemble_final", "scripts/06_assemble_final.py")
    ffmpeg_calls = []

    def fake_run(cmd, check):
        ffmpeg_calls.append(cmd)

    def fake_adjust_speed(input_wav, target_dur_sec, output_wav, min_speed_ratio):
        shutil.copyfile(input_wav, output_wav)
        return False

    monkeypatch.setattr(assemble_stage.subprocess, "run", fake_run)
    monkeypatch.setattr(assemble_stage, "adjust_speed_smart", fake_adjust_speed)
    monkeypatch.setattr(sys, "argv", ["06_assemble_final.py", "--config", str(config_path)])
    assemble_stage.main()

    assert temp_wav.exists()
    assert ffmpeg_calls
    assert ffmpeg_calls[0][0] == "ffmpeg"
