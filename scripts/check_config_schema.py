from __future__ import annotations

import argparse
import json
import sys

from common import load_config
from config_schema import has_errors, render_issues, summarize_issues, validate_config_schema


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the YAML config schema without checking local files or executables")
    parser.add_argument("--config", default="configs/default.yaml", help="Path to YAML config file")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--no-summary", action="store_true", help="Do not print the final summary line")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    issues = validate_config_schema(cfg)

    if args.json:
        payload = {
            "summary": summarize_issues(issues),
            "issues": [issue.to_dict() for issue in issues],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if issues:
            print(render_issues(issues, include_summary=not args.no_summary))
        elif not args.no_summary:
            print("[SUMMARY] ERROR=0 WARN=0 INFO=0")

    return 1 if has_errors(issues) else 0


if __name__ == "__main__":
    sys.exit(main())
