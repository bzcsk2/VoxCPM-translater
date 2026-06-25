from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any

import aiohttp

from common import ensure_dir, env_api_key, get_nested, load_config, parse_args

SYSTEM_PROMPT = """You are a senior script supervisor and professional dubbing translator with expertise in Chinese drama, film, and serialized content across all genres.

Process a JSON array of ASR-transcribed segments in two passes before producing output.

PASS 1 — GLOBAL COMPREHENSION
Read all segments first. Infer genre, setting, character roster, speaker register, emotional continuity, scene boundaries, proper nouns, and likely ASR errors. Pay special attention to Chinese homophones, dropped negation words, repeated artifacts, broken sentence boundaries, and genre vocabulary.

PASS 2 — SEGMENT PROCESSING
For each segment, create:
- zh_fixed: corrected Chinese with natural punctuation and preserved meaning.
- en: professional English dubbing translation, not literal subtitle translation.

Rules:
- Preserve id, start, end, speaker, and text_zh exactly.
- Preserve bracketed markers such as [Music], [Human Sounds], [Silence].
- For [Music] / [Human Sounds] / [Silence], copy the marker as-is.
- For [Lyric], keep the [Lyric] prefix and translate the lyric content.
- Keep character names and numerical values consistent.
- Translation should prioritize voice performance, emotional tone, and spoken rhythm.

Output a single raw JSON array only. No markdown fences. No explanation.
"""

IMMUTABLE_KEYS = ["id", "start", "end", "speaker", "text_zh"]


def _clean_json_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_llm_json_response(content: str) -> list[dict[str, Any]]:
    """Parse a JSON array from common LLM response variants."""
    cleaned = _clean_json_text(content)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(cleaned[start : end + 1])

    if not isinstance(parsed, list):
        raise ValueError("LLM response must be a JSON array")
    for idx, row in enumerate(parsed):
        if not isinstance(row, dict):
            raise ValueError(f"LLM response row {idx} is not an object")
    return parsed


def validate_batch_output(batch: list[dict[str, Any]], output: list[dict[str, Any]]) -> None:
    if len(batch) != len(output):
        raise ValueError(f"batch has {len(batch)} rows, output has {len(output)} rows")
    for idx, (src, out) in enumerate(zip(batch, output)):
        for key in IMMUTABLE_KEYS:
            if src.get(key) != out.get(key):
                raise ValueError(f"row {idx} key {key!r} mismatch: {src.get(key)!r} != {out.get(key)!r}")
        if "zh_fixed" not in out or "en" not in out:
            raise ValueError(f"row {idx} missing zh_fixed or en")


def _failure_dir(cfg: dict[str, Any]) -> Path:
    output_dir = Path(get_nested(cfg, "paths.output_dir", "outputs"))
    return ensure_dir(output_dir / "failed_llm_batches")


def _write_failure(cfg: dict[str, Any], batch_label: str, attempt: int, content: str) -> None:
    path = _failure_dir(cfg) / f"batch_{batch_label}_attempt_{attempt}.txt"
    path.write_text(content, encoding="utf-8")


async def _call_llm(session: aiohttp.ClientSession, cfg: dict[str, Any], batch: list[dict[str, Any]]) -> str:
    url = get_nested(cfg, "llm.api_base")
    model = get_nested(cfg, "llm.model")
    api_key = env_api_key(cfg)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(batch, ensure_ascii=False)},
        ],
        "temperature": get_nested(cfg, "llm.temperature", 0.1),
        "max_tokens": get_nested(cfg, "llm.max_tokens", 8192),
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with session.post(url, json=payload, headers=headers, timeout=300) as resp:
        body = await resp.text()
        if resp.status != 200:
            raise RuntimeError(f"LLM HTTP {resp.status}: {body[:500]}")
        data = json.loads(body)
        return data["choices"][0]["message"]["content"]


async def process_batch(
    session: aiohttp.ClientSession,
    cfg: dict[str, Any],
    batch: list[dict[str, Any]],
    batch_label: str = "0",
) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            content = await _call_llm(session, cfg, batch)
            output = parse_llm_json_response(content)
            validate_batch_output(batch, output)
            return output
        except Exception as exc:
            last_error = exc
            print(f"Batch {batch_label} attempt {attempt} failed: {exc}")
            _write_failure(cfg, batch_label, attempt, str(exc))
            await asyncio.sleep(3)

    split_failed_batches = bool(get_nested(cfg, "llm.split_failed_batches", True))
    if split_failed_batches and len(batch) > 1:
        mid = len(batch) // 2
        print(f"Splitting failed batch {batch_label} into {len(batch[:mid])} + {len(batch[mid:])} rows")
        left = await process_batch(session, cfg, batch[:mid], f"{batch_label}a")
        right = await process_batch(session, cfg, batch[mid:], f"{batch_label}b")
        return [*left, *right]

    raise RuntimeError(f"LLM batch {batch_label} failed after retries") from last_error


async def main_async() -> None:
    args = parse_args("Refine Chinese ASR text and translate it for dubbing")
    cfg = load_config(args.config)
    input_file = get_nested(cfg, "paths.asr_json")
    output_file = get_nested(cfg, "paths.refined_json")
    batch_size = int(get_nested(cfg, "llm.batch_size", 20))
    ensure_dir(os.path.dirname(output_file) or ".")

    with open(input_file, "r", encoding="utf-8") as f:
        segments = json.load(f)

    processed: list[dict[str, Any]] = []
    async with aiohttp.ClientSession() as session:
        for start in range(0, len(segments), batch_size):
            batch = segments[start : start + batch_size]
            batch_label = str(start // batch_size + 1)
            print(f"Processing batch {batch_label}: {len(batch)} segments")
            processed.extend(await process_batch(session, cfg, batch, batch_label=batch_label))

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

    print(f"Done: {len(processed)} segments -> {output_file}")


if __name__ == "__main__":
    asyncio.run(main_async())
