from __future__ import annotations

import json
import os
import re
import shutil
import subprocess

from pydub import AudioSegment

from common import get_nested, load_config, parse_args, timestamp_to_ms


def is_noise_only(text: str) -> bool:
    return bool(re.match(r"^\[.*\]$", text.strip()))


def run_atempo(input_wav: str, ratio: float, output_wav: str) -> None:
    filters: list[str] = []
    tmp = ratio
    while tmp > 2.0:
        filters.append("atempo=2.0")
        tmp /= 2.0
    while tmp < 0.5:
        filters.append("atempo=0.5")
        tmp /= 0.5
    filters.append(f"atempo={tmp}")
    subprocess.run(["ffmpeg", "-y", "-i", input_wav, "-filter:a", ",".join(filters), output_wav], check=True)


def adjust_speed_smart(input_wav: str, target_dur_sec: float, output_wav: str, min_speed_ratio: float) -> None:
    audio = AudioSegment.from_file(input_wav)
    current_dur = len(audio) / 1000.0
    if current_dur <= 0 or target_dur_sec <= 0:
        shutil.copyfile(input_wav, output_wav)
        return
    ratio = current_dur / target_dur_sec
    final_ratio = ratio if ratio > 1.0 else max(min_speed_ratio, ratio)
    if 0.98 < final_ratio < 1.02:
        shutil.copyfile(input_wav, output_wav)
        return
    run_atempo(input_wav, final_ratio, output_wav)


def main() -> None:
    args = parse_args("Assemble generated chunks and mux with source video")
    cfg = load_config(args.config)
    json_file = get_nested(cfg, "paths.refined_json")
    bgm_path = get_nested(cfg, "paths.instrumental_audio")
    chunk_dir = get_nested(cfg, "paths.dub_chunk_dir")
    output_video = get_nested(cfg, "paths.final_video")
    video_source = get_nested(cfg, "paths.input_video")
    temp_mixed_wav = get_nested(cfg, "paths.temp_mixed_wav")
    min_speed_ratio = float(get_nested(cfg, "assembly.min_speed_ratio", 0.70))
    bitrate = get_nested(cfg, "assembly.audio_bitrate", "192k")

    with open(json_file, "r", encoding="utf-8") as f:
        segments = json.load(f)

    final_audio = AudioSegment.from_wav(bgm_path)
    for seg in segments:
        seg_id = seg["id"]
        if is_noise_only(seg.get("en", "")):
            continue
        raw_wav = os.path.join(chunk_dir, f"raw_{seg_id}.wav")
        if not os.path.exists(raw_wav):
            raw_wav = os.path.join(chunk_dir, f"dub_{seg_id}.wav")
        if not os.path.exists(raw_wav):
            print(f"Missing chunk: ID_{seg_id}")
            continue
        start_ms = timestamp_to_ms(seg["start"])
        end_ms = timestamp_to_ms(seg["end"])
        fixed_wav = os.path.join(chunk_dir, f"fixed_{seg_id}.wav")
        adjust_speed_smart(raw_wav, (end_ms - start_ms) / 1000.0, fixed_wav, min_speed_ratio)
        final_audio = final_audio.overlay(AudioSegment.from_wav(fixed_wav), position=start_ms)

    final_audio.export(temp_mixed_wav, format="wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", video_source, "-i", temp_mixed_wav,
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", bitrate, output_video,
    ], check=True)
    print(f"Done: {output_video}")


if __name__ == "__main__":
    main()
