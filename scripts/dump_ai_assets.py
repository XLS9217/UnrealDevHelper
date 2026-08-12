"""Dump partial and full Blackboard, Behavior Tree, and EQS inspection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.application import UnrealApplication


ASSETS = {
    "BB_AgenticAI": {
        "asset_path": "/Game/TheAgentGame/AI/BB_AgenticAI",
        "node": "/keys",
    },
    "BT_AgenticAI": {
        "asset_path": "/Game/TheAgentGame/AI/BT_AgenticAI",
        "node": "/graph",
    },
    "EQ_FindPointAroundTarget": {
        "asset_path": "/Game/TheAgentGame/AI/EQ_FindPointAroundTarget",
        "node": "/graph",
    },
}


def dump(path: Path, result: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(path)

    inspection = result.get("inspection", {})
    if not inspection.get("ok"):
        error = inspection.get("error", {})
        raise RuntimeError(
            f"{error.get('code', 'inspection_failed')}: "
            f"{error.get('message', 'unknown inspection error')}"
        )


def main() -> None:
    application = UnrealApplication()
    output_dir = Path(__file__).resolve().parent

    for name, request in ASSETS.items():
        for full in (False, True):
            suffix = "full" if full else "partial"
            dump(
                output_dir / f"{name}_{suffix}.json",
                application.inspect_uasset_detail(
                    request["asset_path"],
                    node=request["node"],
                    full=full,
                ),
            )


if __name__ == "__main__":
    main()
