from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from common import load_config, parse_args


def main() -> None:
    args = parse_args("Compatibility wrapper: run refinement with Kimi K2 Thinking on NVIDIA")
    cfg = load_config(args.config)
    cfg.setdefault("llm", {})["model"] = "moonshotai/kimi-k2-thinking"

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".yaml", delete=False) as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
        tmp_config = f.name

    try:
        script = Path(__file__).with_name("03_refine_and_translate.py")
        subprocess.run([sys.executable, str(script), "--config", tmp_config], check=True)
    finally:
        try:
            os.remove(tmp_config)
        except OSError:
            pass


if __name__ == "__main__":
    main()
