from __future__ import annotations

import argparse
import json
import sys

from stage_contracts import all_stage_contracts, validate_stage_contracts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List pipeline stage contracts")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser.parse_args()


def render_table() -> str:
    lines = [
        "| ID | Name | Optional | Auto-resumable | Outputs | Description |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for contract in all_stage_contracts():
        outputs = ", ".join(contract.output_keys) if contract.output_keys else "-"
        lines.append(
            f"| {contract.id} | `{contract.name}` | {str(contract.optional).lower()} | "
            f"{str(contract.auto_resumable).lower()} | `{outputs}` | {contract.description} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    errors = validate_stage_contracts()
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps([contract.to_dict() for contract in all_stage_contracts()], ensure_ascii=False, indent=2))
    else:
        print(render_table(), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
