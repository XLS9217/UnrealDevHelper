"""Application operations exposed by the CLI frontend."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Iterator, Mapping

from .backend import UnrealBackend, UnrealRemoteBackend


RESULT_MARKER = "UNREALDEVHELPER_RESULT:"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "unreal_scripts"
_VARIABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


def marked_result(response: dict[str, Any]) -> Any:
    """Extract a JSON value logged with ``RESULT_MARKER``."""
    # Unreal echoes the submitted source in ``command``. A script containing
    # the marker literal therefore produces a false match before its output.
    # Search output first and accept only a marker followed by valid JSON.
    output = response.get("output", [])
    remaining = {
        key: value
        for key, value in response.items()
        if key not in {"command", "output"}
    }
    invalid_payloads: list[str] = []
    for value in _strings([output, remaining]):
        for line in value.splitlines():
            marker_at = line.find(RESULT_MARKER)
            if marker_at >= 0:
                payload = line[marker_at + len(RESULT_MARKER) :].strip()
                try:
                    return json.loads(payload)
                except json.JSONDecodeError:
                    invalid_payloads.append(payload)
    if invalid_payloads:
        raise RuntimeError(
            "Unreal returned a result marker without valid JSON. "
            f"First payload: {invalid_payloads[0]!r}"
        )
    raise RuntimeError(
        "The Unreal script completed without returning a marked result. "
        f"Remote response: {response!r}"
    )


class UnrealApplication:
    """Allowlisted use cases exposed by the backend daemon."""

    def __init__(
        self,
        backend: UnrealBackend | None = None,
        *,
        scripts_dir: Path = SCRIPTS_DIR,
    ) -> None:
        self.backend = backend or UnrealRemoteBackend()
        self.scripts_dir = scripts_dir.resolve()

    def status(self, wait_seconds: float = 1.5) -> dict[str, Any]:
        nodes = self.backend.discover(wait_seconds=max(0.0, min(wait_seconds, 10.0)))
        return {"connected": bool(nodes), "nodes": nodes}

    def execute_python(
        self,
        code: str,
        *,
        node_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute Python supplied by an agent for read-only inspection."""
        if not code.strip():
            raise ValueError("Python source must not be empty.")
        return self.backend.execute(code, node_id=node_id)

    def _execute_script(
        self,
        script_name: str,
        *,
        variables: Mapping[str, Any] | None = None,
        node_id: str | None = None,
        raw_response: bool = False,
    ) -> Any:
        script_path = (self.scripts_dir / script_name).resolve()
        try:
            script_path.relative_to(self.scripts_dir)
        except ValueError as exc:
            raise ValueError("Script must be inside the unreal_scripts directory.") from exc
        if script_path.suffix.lower() != ".py" or not script_path.is_file():
            raise FileNotFoundError(f"Unreal script not found: {script_name}")

        assignments: list[str] = []
        for name, value in (variables or {}).items():
            if not _VARIABLE_NAME.fullmatch(name):
                raise ValueError(f"Invalid script variable name: {name!r}")
            assignments.append(f"{name} = {value!r}")

        script = script_path.read_text(encoding="utf-8")
        source = "\n".join(assignments + (["", script] if assignments else [script]))
        response = self.backend.execute(source, node_id=node_id)
        return response if raw_response else marked_result(response)

    def blueprint_info(
        self,
        asset_path: str,
        *,
        include_private: bool = False,
        max_depth: int = 3,
        max_items: int = 128,
        node_id: str | None = None,
    ) -> dict[str, Any]:
        return self._execute_script(
            "blueprint_info.py",
            variables={
                "BLUEPRINT_PATH": asset_path,
                "INCLUDE_PRIVATE": bool(include_private),
                "MAX_DEPTH": max(0, min(int(max_depth), 8)),
                "MAX_ITEMS": max(1, min(int(max_items), 2048)),
            },
            node_id=node_id,
        )
