"""Small adapter around Unreal Engine's bundled ``remote_execution.py``."""

from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path
import threading
import time
from types import ModuleType
from typing import Any

import psutil


class UnrealRemoteError(RuntimeError):
    """Raised when Unreal remote execution cannot complete a request."""


def _candidate_module_paths() -> list[Path]:
    candidates: list[Path] = []
    explicit = os.environ.get("UNREAL_REMOTE_EXECUTION_PATH")
    if explicit:
        path = Path(explicit).expanduser()
        candidates.append(path / "remote_execution.py" if path.is_dir() else path)

    engine_root = os.environ.get("UNREAL_ENGINE_ROOT")
    if engine_root:
        root = Path(engine_root).expanduser()
        candidates.extend(
            [
                root
                / "Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py",
                root
                / "Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py",
            ]
        )

    # An MCP tool call only needs the helper when an Editor should already be
    # running. Derive the Engine directory from that process so normal setup
    # requires only the absolute path to this repository.
    for process in psutil.process_iter(["name", "exe"]):
        try:
            name = (process.info.get("name") or "").lower()
            executable = process.info.get("exe")
            if not executable or "unrealeditor" not in name:
                continue
            exe_path = Path(executable)
            engine_dir = next(
                (parent for parent in exe_path.parents if parent.name.lower() == "engine"),
                None,
            )
            if engine_dir is not None:
                candidates.append(
                    engine_dir
                    / "Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py"
                )
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            continue
    return candidates


def load_remote_execution() -> ModuleType:
    """Load the helper shipped with Unreal, preferring an explicitly selected copy."""
    for path in _candidate_module_paths():
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location("unreal_remote_execution", path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    try:
        return importlib.import_module("remote_execution")
    except ImportError as exc:
        raise UnrealRemoteError(
            "Could not find Unreal's remote_execution.py from a running "
            "UnrealEditor process. Start Unreal Editor, or optionally set "
            "UNREAL_REMOTE_EXECUTION_PATH/UNREAL_ENGINE_ROOT as an override."
        ) from exc


class UnrealRemoteClient:
    """Discover an editor node and execute one command at a time."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def discover(self, wait_seconds: float = 1.5) -> list[dict[str, Any]]:
        module = load_remote_execution()
        remote = module.RemoteExecution()
        remote.start()
        try:
            deadline = time.monotonic() + max(0.0, wait_seconds)
            nodes = list(remote.remote_nodes)
            while not nodes and time.monotonic() < deadline:
                time.sleep(0.1)
                nodes = list(remote.remote_nodes)
            return [dict(node) for node in nodes]
        finally:
            remote.stop()

    def run(
        self,
        command: str,
        *,
        node_id: str | None = None,
        wait_seconds: float = 2.0,
    ) -> dict[str, Any]:
        """Execute Python in Unreal's embedded interpreter."""
        with self._lock:
            module = load_remote_execution()
            remote = module.RemoteExecution()
            remote.start()
            try:
                deadline = time.monotonic() + max(0.0, wait_seconds)
                nodes = list(remote.remote_nodes)
                while not nodes and time.monotonic() < deadline:
                    time.sleep(0.1)
                    nodes = list(remote.remote_nodes)
                if not nodes:
                    raise UnrealRemoteError(
                        "No Unreal Editor remote-execution node was discovered. "
                        "Ensure the editor is running and Python Remote Execution is enabled."
                    )

                selected_id = node_id or os.environ.get("UNREAL_REMOTE_NODE_ID")
                if selected_id is None:
                    selected_id = str(nodes[0]["node_id"])
                elif not any(str(node.get("node_id")) == selected_id for node in nodes):
                    raise UnrealRemoteError(
                        f"Unreal node {selected_id!r} was not found; discovered "
                        f"{[node.get('node_id') for node in nodes]!r}."
                    )

                remote.open_command_connection(selected_id)
                has_connection = getattr(remote, "has_command_connection", None)
                if callable(has_connection) and not has_connection():
                    raise UnrealRemoteError(
                        f"Could not open a command connection to Unreal node {selected_id}."
                    )

                mode = getattr(module, "MODE_EXEC_FILE", "ExecuteFile")
                response = remote.run_command(
                    command,
                    unattended=True,
                    exec_mode=mode,
                )
                if not isinstance(response, dict):
                    raise UnrealRemoteError(
                        f"Unreal returned an unexpected response: {response!r}"
                    )
                if response.get("success") is False:
                    raise UnrealRemoteError(
                        f"Unreal rejected the Python command: {response!r}"
                    )
                return response
            finally:
                remote.stop()
