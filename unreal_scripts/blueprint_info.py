"""Return JSON-safe information about a Blueprint class default object.

The MCP server injects BLUEPRINT_PATH, INCLUDE_PRIVATE, MAX_DEPTH, and
MAX_ITEMS before executing this file inside Unreal Editor.
"""

import json

import unreal


_RESULT_MARKER = "UNREALDEVHELPER_RESULT:"


def _serialize(value, depth=0, seen=None):
    if seen is None:
        seen = set()
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if depth >= MAX_DEPTH:
        return str(value)

    value_id = id(value)
    if value_id in seen:
        return "<recursive>"

    if isinstance(value, dict):
        seen.add(value_id)
        result = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= MAX_ITEMS:
                result["<truncated>"] = len(value) - MAX_ITEMS
                break
            result[str(key)] = _serialize(item, depth + 1, seen)
        seen.discard(value_id)
        return result

    if isinstance(value, (list, tuple, set)):
        seen.add(value_id)
        result = [
            _serialize(item, depth + 1, seen)
            for item in list(value)[:MAX_ITEMS]
        ]
        if len(value) > MAX_ITEMS:
            result.append("<truncated: {} more>".format(len(value) - MAX_ITEMS))
        seen.discard(value_id)
        return result

    if isinstance(value, unreal.Object):
        return {
            "object_path": value.get_path_name(),
            "class": value.get_class().get_path_name(),
        }

    # Unreal value types (Name, Text, structs, enums) generally have useful
    # string representations even when they are not JSON-native.
    return str(value)


def _read_properties(default_object):
    properties = {}
    for name in sorted(dir(default_object)):
        if name.startswith("_") and not INCLUDE_PRIVATE:
            continue
        try:
            value = default_object.get_editor_property(name)
        except Exception:
            continue
        properties[name] = _serialize(value)
    return properties


def _load_generated_class(asset_path):
    asset = unreal.load_asset(asset_path)
    if isinstance(asset, unreal.Blueprint):
        generated_class = asset.generated_class()
        return asset, generated_class

    generated_class = unreal.EditorAssetLibrary.load_blueprint_class(asset_path)
    if generated_class:
        return asset, generated_class
    raise RuntimeError("Blueprint could not be loaded: {}".format(asset_path))


def main():
    asset, generated_class = _load_generated_class(BLUEPRINT_PATH)
    if not generated_class:
        raise RuntimeError(
            "Blueprint has no generated class: {}".format(BLUEPRINT_PATH)
        )

    default_object = unreal.get_default_object(generated_class)
    result = {
        "asset_path": asset.get_path_name() if asset else BLUEPRINT_PATH,
        "generated_class": generated_class.get_path_name(),
        "default_object": default_object.get_path_name(),
        "properties": _read_properties(default_object),
    }
    unreal.log(_RESULT_MARKER + json.dumps(result, ensure_ascii=False))


main()
