import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("assemble_final", ROOT / "scripts" / "06_assemble_final.py")
assemble_final = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(assemble_final)


def test_find_chunk_prefers_raw_over_dub(tmp_path: Path) -> None:
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    raw = chunk_dir / "raw_3.wav"
    dub = chunk_dir / "dub_3.wav"
    raw.write_bytes(b"raw")
    dub.write_bytes(b"dub")

    assert assemble_final.find_chunk(chunk_dir, 3) == str(raw)


def test_is_noise_only_keeps_legacy_bracket_behavior() -> None:
    assert assemble_final.is_noise_only("[Music]")
    assert assemble_final.is_noise_only("[Lyric]")
    assert not assemble_final.is_noise_only("Hello")


def test_validate_assembly_inputs_rejects_bad_missing_policy(tmp_path: Path) -> None:
    refined = tmp_path / "refined.json"
    bgm = tmp_path / "instrumental.wav"
    video = tmp_path / "input.mp4"
    chunks = tmp_path / "chunks"
    chunks.mkdir()
    refined.write_text("[]", encoding="utf-8")
    bgm.write_bytes(b"wav")
    video.write_bytes(b"video")

    with pytest.raises(ValueError):
        assemble_final.validate_assembly_inputs(
            str(refined),
            str(bgm),
            str(chunks),
            str(video),
            str(tmp_path / "mixed.wav"),
            str(tmp_path / "out.mp4"),
            0.7,
            "invalid",
        )


def test_validate_refined_segments_accepts_minimal_assembly_contract() -> None:
    assemble_final.validate_refined_segments(
        [
            {
                "id": 0,
                "start": "00:00:00.000",
                "end": "00:00:01.000",
                "en": "Hello.",
            }
        ]
    )


def test_validate_refined_segments_rejects_bad_contract() -> None:
    with pytest.raises(ValueError):
        assemble_final.validate_refined_segments([{"id": 0}])


def test_missing_assembly_chunk_ids_skips_bracket_rows(tmp_path: Path) -> None:
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    segments = [
        {"id": 0, "start": "00:00:00.000", "end": "00:00:01.000", "en": "[Lyric]"},
        {"id": 1, "start": "00:00:01.000", "end": "00:00:02.000", "en": "Hello."},
    ]

    assert assemble_final.missing_assembly_chunk_ids(segments, chunk_dir) == [1]


def test_atempo_filters_splits_out_of_range_ratios() -> None:
    assert assemble_final.atempo_filters(4.0) == ["atempo=2.0", "atempo=2.0"]
    assert assemble_final.atempo_filters(0.25) == ["atempo=0.5", "atempo=0.5"]
