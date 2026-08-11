"""Inspect one asset through UnrealDevHelperPlugin without modifying it.

The application layer injects ASSET_PATH before executing this file inside
Unreal Editor's embedded Python interpreter.
"""

import json

import unreal


_RESULT_MARKER = "UNREALDEVHELPER_RESULT:"


def main():
    raw_result = unreal.UnrealDevHelperLibrary.inspect_uasset(ASSET_PATH)
    try:
        inspection = json.loads(raw_result)
    except (TypeError, json.JSONDecodeError) as exc:
        inspection = {
            "ok": False,
            "error": {
                "code": "invalid_plugin_response",
                "message": str(exc),
                "raw_result": str(raw_result),
            },
        }

    result = {"asset_path": ASSET_PATH, "inspection": inspection}
    unreal.log(_RESULT_MARKER + json.dumps(result, ensure_ascii=False))


main()
