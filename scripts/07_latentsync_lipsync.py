from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from common import ensure_dir, get_nested, load_config, parse_args


def main() -> None:
    args = parse_args("Optional LatentSync lip-sync step")
    cfg = load_config(args.config)

    latentsync_dir = Path(get_nested(cfg, "models.latentsync_dir"))
    video_input = get_nested(cfg, "paths.input_video")
    audio_input = get_nested(cfg, "paths.temp_mixed_wav")
    video_output = get_nested(cfg, "paths.lipsync_video")
    ensure_dir(Path(video_output).parent)

    inference_py = latentsync_dir / "scripts" / "inference.py"
    if not inference_py.exists():
        raise FileNotFoundError(f"LatentSync inference script not found: {inference_py}")

    cmd = [sys.executable, str(inference_py), "--video_path", video_input, "--audio_path", audio_input, "--video_out_path", video_output]
    env = os.environ.copy()
    env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    subprocess.run(cmd, check=True, env=env)
    print(f"Done: {video_output}")


if __name__ == "__main__":
    main()
