import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("refine_translate", ROOT / "scripts" / "03_refine_and_translate.py")
refine_translate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(refine_translate)


def test_parse_llm_json_response_accepts_raw_array() -> None:
    parsed = refine_translate.parse_llm_json_response('[{"id": 0, "en": "Hello."}]')
    assert parsed == [{"id": 0, "en": "Hello."}]


def test_parse_llm_json_response_strips_markdown_fence() -> None:
    parsed = refine_translate.parse_llm_json_response('```json\n[{"id": 0, "en": "Hello."}]\n```')
    assert parsed == [{"id": 0, "en": "Hello."}]


def test_parse_llm_json_response_extracts_array_from_extra_text() -> None:
    parsed = refine_translate.parse_llm_json_response('Here is the result:\n[{"id": 1, "en": "Go."}]\nDone.')
    assert parsed == [{"id": 1, "en": "Go."}]


def test_validate_batch_output_rejects_alignment_drift() -> None:
    batch = [{"id": 0, "start": "00:00:00.000", "end": "00:00:01.000", "speaker": "A", "text_zh": "你好"}]
    output = [{**batch[0], "id": 1, "zh_fixed": "你好。", "en": "Hello."}]
    try:
        refine_translate.validate_batch_output(batch, output)
    except ValueError as exc:
        assert "id" in str(exc)
    else:
        raise AssertionError("expected alignment validation failure")
