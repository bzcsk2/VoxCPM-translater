from __future__ import annotations

import json
import os
import sys
import time

import torch

from common import ensure_dir, get_nested, load_config, parse_args, seconds_to_timestamp


def main() -> None:
    args = parse_args("Transcribe vocals with VibeVoice-ASR")
    cfg = load_config(args.config)

    vibe_repo = get_nested(cfg, "models.vibevoice_repo")
    if vibe_repo and vibe_repo not in sys.path:
        sys.path.append(vibe_repo)

    from vibevoice.modular.modeling_vibevoice_asr import VibeVoiceASRForConditionalGeneration
    from vibevoice.processor.vibevoice_asr_processor import VibeVoiceASRProcessor

    model_path = get_nested(cfg, "models.vibevoice_asr_path")
    qwen_path = get_nested(cfg, "models.qwen_asr_path")
    audio_input = get_nested(cfg, "paths.vocal_source_for_asr")
    output_json = get_nested(cfg, "paths.asr_json")
    device = get_nested(cfg, "runtime.asr_device", "cuda:0")
    dtype_name = get_nested(cfg, "runtime.asr_dtype", "bfloat16")
    dtype = torch.bfloat16 if dtype_name == "bfloat16" else torch.float16

    ensure_dir(os.path.dirname(output_json) or ".")

    print("Loading VibeVoice-ASR...")
    processor = VibeVoiceASRProcessor.from_pretrained(
        model_path,
        trust_remote_code=True,
        language_model_pretrained_name=qwen_path,
    )
    model = VibeVoiceASRForConditionalGeneration.from_pretrained(
        model_path,
        dtype=dtype,
        device_map=device,
        trust_remote_code=True,
    )
    model.eval()

    hint = get_nested(cfg, "asr.context_hint", "This is a drama. Identify speakers carefully.")
    print(f"Transcribing: {audio_input}")
    inputs = processor(
        audio=[audio_input],
        sampling_rate=None,
        return_tensors="pt",
        padding=True,
        add_generation_prompt=True,
        context_info=hint,
    )
    inputs = {k: v.to(model.device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}

    generation_config = {
        "max_new_tokens": get_nested(cfg, "asr.max_new_tokens", 8192),
        "pad_token_id": processor.pad_id,
        "eos_token_id": processor.tokenizer.eos_token_id,
        "do_sample": True,
        "temperature": get_nested(cfg, "asr.temperature", 0.5),
        "top_p": get_nested(cfg, "asr.top_p", 0.95),
        "repetition_penalty": get_nested(cfg, "asr.repetition_penalty", 1.2),
    }

    start = time.time()
    with torch.no_grad():
        output_ids = model.generate(**inputs, **generation_config)

    input_length = inputs["input_ids"].shape[1]
    generated_ids = output_ids[0, input_length:]
    eos_positions = (generated_ids == processor.tokenizer.eos_token_id).nonzero(as_tuple=True)[0]
    if len(eos_positions) > 0:
        generated_ids = generated_ids[: eos_positions[0] + 1]

    raw_text = processor.decode(generated_ids, skip_special_tokens=True)
    segments = processor.post_process_transcription(raw_text)

    final_results = []
    for i, seg in enumerate(segments):
        start_sec = float(seg.get("start_time", 0))
        end_sec = float(seg.get("end_time", 0))
        final_results.append(
            {
                "id": i,
                "start": seconds_to_timestamp(start_sec),
                "end": seconds_to_timestamp(end_sec),
                "speaker": seg.get("speaker_id", "Unknown"),
                "text_zh": seg.get("text", "").strip(),
            }
        )

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)

    print(f"Done: {len(final_results)} segments -> {output_json} ({time.time() - start:.1f}s)")


if __name__ == "__main__":
    main()
