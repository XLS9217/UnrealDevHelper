"""Connection to Unreal Engine's bundled remote_execution.py."""

from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path
import time
from types import ModuleType
from typing import Any, Protocol


class UnrealBackend(Protocol):
    """Transport required by UnrealApplication."""

    def discover(self, wait_seconds: float = 1.5) -> list[dict[str, Any]]: ...

    def execute(self, command: str, wait_seconds: float = 2.0) -> dict[str, Any]: ...


class UnrealRemoteError(RuntimeError):
    """Raised when Unreal remote execution fails."""


def _load_project_env() -> None:
    """Load simple KEY=VALUE settings from the repository .env file."""
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.is_file():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _remote_execution_from_editor(editor_executable: Path) -> Path | None:
    engine_dir = next(
        (parent for parent in editor_executable.parents if parent.name.lower() == "engine"),
        None,
    )
    if engine_dir is None:
        return None
    return engine_dir / "Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py"


def load_remote_execution(editor_executable: str | Path | None = None) -> ModuleType:
    """Load remote_execution.py from explicit configuration or the environment."""
    _load_project_env()
    candidates: list[Path] = []
    explicit = os.environ.get("UNREAL_REMOTE_EXECUTION_PATH")
    if explicit:
        path = Path(explicit).expanduser()
        candidates.append(path / "remote_execution.py" if path.is_dir() else path)

    selected_editor = editor_executable or os.environ.get("UNREAL_EDITOR_EXE")
    if selected_editor:
        candidate = _remote_execution_from_editor(Path(selected_editor).expanduser().resolve())
        if candidate is not None:
            candidates.append(candidate)

    engine_root = os.environ.get("UNREAL_ENGINE_ROOT")
    if engine_root:
        candidates.append(
            Path(engine_root).expanduser()
            / "Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py"
        )

    for path in candidates:
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location("unreal_remote_execution", path)
        if spec is not None and spec.loader is not None:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

    try:
        return importlib.import_module("remote_execution")
    except ImportError as exc:
        raise UnrealRemoteError(
            "Could not find remote_execution.py. Supply --unreal-exe or set "
            "UNREAL_EDITOR_EXE, UNREAL_ENGINE_ROOT, or UNREAL_REMOTE_EXECUTION_PATH."
        ) from exc


class UnrealRemoteBackend:
    """Connect to the single open Unreal Editor instance."""

    def __init__(self, editor_executable: str | Path | None = None) -> None:
        self.editor_executable = editor_executable

    def discover(self, wait_seconds: float = 1.5) -> list[dict[str, Any]]:
        remote = self._remote()
        try:
            return [dict(node) for node in self._wait_for_nodes(remote, wait_seconds)]
        finally:
            remote.stop()

    def execute(self, command: str, wait_seconds: float = 2.0) -> dict[str, Any]:
        remote = self._remote()
        try:
            nodes = self._wait_for_nodes(remote, wait_seconds)
            if not nodes:
                raise UnrealRemoteError(
                    "No Unreal Editor was discovered. Ensure Remote Execution is enabled."
                )

            node_id = str(nodes[0]["node_id"])
            remote.open_command_connection(node_id)
            response = remote.run_command(
                command,
                unattended=True,
                exec_mode=getattr(self._module, "MODE_EXEC_FILE", "ExecuteFile"),
            )
            if not isinstance(response, dict) or response.get("success") is False:
                raise UnrealRemoteError(f"Unreal rejected the command: {response!r}")
            return response
        finally:
            remote.stop()

    def _remote(self):
        self._module = load_remote_execution(self.editor_executable)
        remote = self._module.RemoteExecution()
        remote.start()
        return remote

    @staticmethod
    def _wait_for_nodes(remote: Any, wait_seconds: float) -> list[dict[str, Any]]:
        deadline = time.monotonic() + max(0.0, wait_seconds)
        nodes = list(remote.remote_nodes)
        while not nodes and time.monotonic() < deadline:
            time.sleep(0.1)
            nodes = list(remote.remote_nodes)
        return nodes
