"""Test every supported native inspector and dump JSON beside this script."""

from __future__ import annotations

import json
from pathlib import Path

from src.application import UnrealApplication


ASSETS = {
    "BB_AgenticAI.json": "/Game/TheAgentGame/AI/BB_AgenticAI",
    "BT_AgenticAI.json": "/Game/TheAgentGame/AI/BT_AgenticAI",
    "BP_TopDownCharacter.json": "/Game/TopDown/Blueprints/BP_TopDownCharacter",
    "BP_AgenticCharacter.json": "/Game/TheAgentGame/BP_AgenticCharacter",
    "EQ_FindPointAroundTarget.json": "/Game/TheAgentGame/AI/EQ_FindPointAroundTarget",
}


def main() -> None:
    application = UnrealApplication()
    output_dir = Path(__file__).resolve().parent
    failures = []

    for filename, asset_path in ASSETS.items():
        result = application.inspect_uasset(asset_path)
        path = output_dir / filename
        path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(path)
        inspection = result.get("inspection", {})
        if not inspection.get("ok"):
            error = inspection.get("error", {})
            failures.append(f"{asset_path}: {error.get('code', 'unknown_error')}")

    if failures:
        raise RuntimeError("Inspection failed:\n" + "\n".join(failures))


if __name__ == "__main__":
    main()
