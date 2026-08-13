"""Dump full and processed examples of each Anim Blueprint graph kind."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.application import UnrealApplication


ASSET_PATH = "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed"
GRAPHS = {
    "EventGraph": "/graphs/EventGraph",
    "AnimGraph": "/graphs/AnimGraph",
    "StateMachine_MainStates": "/graphs/Main States",
}
OUTPUT_DIR = Path(__file__).resolve().parent


def dump(path: Path, result: dict[str, Any]) -> None:
    inspection = result.get("inspection", {})
    if not inspection.get("ok"):
        error = inspection.get("error", {})
        raise RuntimeError(
            f"{error.get('code', 'inspection_failed')}: "
            f"{error.get('message', 'unknown inspection error')}"
        )
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(path)


def main() -> None:
    application = UnrealApplication()
    for name, node in GRAPHS.items():
        dump(
            OUTPUT_DIR / f"{name}_full.json",
            application.inspect_uasset_detail(ASSET_PATH, node=node, full=True),
        )
        dump(
            OUTPUT_DIR / f"{name}_processed.json",
            application.inspect_uasset_detail(ASSET_PATH, node=node, full=False),
        )
    dump(
        OUTPUT_DIR / "AnimAssets_full.json",
        application.inspect_uasset_detail(ASSET_PATH, node="/anim_assets", full=True),
    )
    dump(
        OUTPUT_DIR / "AnimAssets_processed.json",
        application.inspect_uasset_detail(ASSET_PATH, node="/anim_assets", full=False),
    )


if __name__ == "__main__":
    main()
