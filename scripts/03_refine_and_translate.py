from __future__ import annotations

import asyncio
import json
import os
import re
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


def _clean_json_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def process_batch(session: aiohttp.ClientSession, cfg: dict[str, Any], batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
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

    for attempt in range(3):
        try:
            async with session.post(url, json=payload, headers=headers, timeout=300) as resp:
                body = await resp.text()
                if resp.status != 200:
                    print(f"LLM HTTP {resp.status}: {body[:500]}")
                    await asyncio.sleep(3)
                    continue
                data = json.loads(body)
                content = data["choices"][0]["message"]["content"]
                return json.loads(_clean_json_text(content))
        except Exception as exc:
            print(f"Batch attempt {attempt + 1} failed: {exc}")
            await asyncio.sleep(3)
    raise RuntimeError("LLM batch failed after 3 attempts")


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
            print(f"Processing batch {start // batch_size + 1}: {len(batch)} segments")
            processed.extend(await process_batch(session, cfg, batch))

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

    print(f"Done: {len(processed)} segments -> {output_file}")


if __name__ == "__main__":
    asyncio.run(main_async())
