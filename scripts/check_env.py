from __future__ import annotations

import argparse
import json
import sys

from common import load_config
from config_checks import CheckResult, has_failures, render_results, run_environment_checks, summarize_results


def parse_check_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check local environment and config before running the pipeline")
    parser.add_argument("--config", default="configs/default.yaml", help="Path to YAML config file")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON results")
    parser.add_argument("--no-summary", action="store_true", help="Do not print the final summary line")
    return parser.parse_args()


def run_checks(config_path: str) -> list[CheckResult]:
    cfg = load_config(config_path)
    return run_environment_checks(cfg)


def main() -> int:
    args = parse_check_args()
    results = run_checks(args.config)

    if args.json:
        payload = {
            "summary": summarize_results(results),
            "results": [result.to_dict() for result in results],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_results(results, include_summary=not args.no_summary))

    return 1 if has_failures(results) else 0


if __name__ == "__main__":
    sys.exit(main())
