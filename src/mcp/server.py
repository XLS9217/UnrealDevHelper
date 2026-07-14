"""Stdio MCP server exposing Unreal Editor Python operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from mcp.server.fastmcp import FastMCP

from remote import UnrealRemoteClient


RESULT_MARKER = "UNREALDEVHELPER_RESULT:"
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "unreal_scripts"

mcp = FastMCP("Unreal Dev Helper")
client = UnrealRemoteClient()


def _strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


def _marked_result(response: dict[str, Any]) -> dict[str, Any]:
    for value in _strings(response):
        for line in value.splitlines():
            marker_at = line.find(RESULT_MARKER)
            if marker_at >= 0:
                payload = line[marker_at + len(RESULT_MARKER) :].strip()
                return json.loads(payload)
    raise RuntimeError(
        "The Unreal script completed without returning a marked result. "
        f"Remote response: {response!r}"
    )


@mcp.tool()
def unreal_status(wait_seconds: float = 1.5) -> dict[str, Any]:
    """Discover Unreal Editor instances available to this MCP server.

    Use this before other Unreal tools and after an Editor restart. If multiple
    nodes are returned, select the node matching the target project. Discovery
    is read-only.

    Args:
        wait_seconds: Maximum discovery wait in seconds (0-10). Use 1.5
            normally or 3-5 immediately after starting Unreal Editor.
    """
    nodes = client.discover(wait_seconds=wait_seconds)
    return {"connected": bool(nodes), "nodes": nodes}


@mcp.tool()
def unreal_execute_python(
    code: str,
    node_id: str | None = None,
) -> dict[str, Any]:
    """Execute trusted Python source inside a running Unreal Editor.

    The source runs in Unreal's embedded interpreter where ``import unreal`` is
    available. Prefer specialized tools when possible and do not make
    destructive changes unless the user requested them.

    Args:
        code: Complete Python source without Markdown fences. Emit useful
            results with ``unreal.log()`` and split large output across short
            log lines.
        node_id: Temporary node ID returned by ``unreal_status``. Required when
            multiple Unreal Editors are running; otherwise optional.
    """
    return client.run(code, node_id=node_id)


@mcp.tool()
def blueprint_info(
    asset_path: str,
    include_private: bool = False,
    max_depth: int = 3,
    max_items: int = 128,
    node_id: str | None = None,
) -> dict[str, Any]:
    """Read a Blueprint generated class's default object (CDO), not an instance.

    This is read-only: it does not spawn, compile, edit, or save the Blueprint.

    Args:
        asset_path: Unreal Content Browser path, such as
            ``/Game/TheAgentGame/BP_AgenticCharacter``. Do not pass a Windows
            ``.uasset`` path or the generated ``_C`` class path.
        include_private: Whether to attempt names beginning with ``_``. Leave
            false for normal inspection.
        max_depth: Maximum nested serialization depth (0-8). Use 1 for a compact
            overview or 3 for normal inspection.
        max_items: Maximum elements serialized from each collection (1-2048).
        node_id: Temporary node ID returned by ``unreal_status``. Required when
            multiple Unreal Editors are running; otherwise optional.
    """
    script_path = SCRIPTS_DIR / "blueprint_info.py"
    script = script_path.read_text(encoding="utf-8")
    inputs = "\n".join(
        [
            f"BLUEPRINT_PATH = {asset_path!r}",
            f"INCLUDE_PRIVATE = {bool(include_private)!r}",
            f"MAX_DEPTH = {max(0, min(int(max_depth), 8))!r}",
            f"MAX_ITEMS = {max(1, min(int(max_items), 2048))!r}",
        ]
    )
    response = client.run(f"{inputs}\n\n{script}", node_id=node_id)
    return _marked_result(response)


def main() -> None:
    """Run the MCP server over stdin/stdout."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
