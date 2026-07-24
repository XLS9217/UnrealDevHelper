"""Backend for Unreal Engine's bundled ``remote_execution.py``."""

from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path
import threading
import time
from types import ModuleType
from typing import Any, Protocol

import psutil


class UnrealRemoteError(RuntimeError):
    """Raised when Unreal remote execution cannot complete a request."""


class UnrealBackend(Protocol):
    """Interface consumed by application services and frontend adapters."""

    def discover(self, wait_seconds: float = 1.5) -> list[dict[str, Any]]:
        """Return discoverable Unreal Remote Execution nodes."""

    def execute(
        self,
        command: str,
        *,
        node_id: str | None = None,
        wait_seconds: float = 2.0,
    ) -> dict[str, Any]:
        """Execute Python source in an Unreal node."""


def _remote_execution_from_editor(editor_executable: Path) -> Path | None:
    engine_dir = next(
        (parent for parent in editor_executable.parents if parent.name.lower() == "engine"),
        None,
    )
    if engine_dir is None:
        return None
    return (
        engine_dir
        / "Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py"
    )


def _candidate_module_paths(
    *,
    editor_executable: str | Path | None = None,
    allow_process_discovery: bool = False,
) -> list[Path]:
    candidates: list[Path] = []
    explicit = os.environ.get("UNREAL_REMOTE_EXECUTION_PATH")
    if explicit:
        path = Path(explicit).expanduser()
        candidates.append(path / "remote_execution.py" if path.is_dir() else path)

    selected_editor = editor_executable or os.environ.get("UNREAL_EDITOR_EXE")
    if selected_editor:
        candidate = _remote_execution_from_editor(
            Path(selected_editor).expanduser().resolve()
        )
        if candidate is not None:
            candidates.append(candidate)

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

    if allow_process_discovery:
        for process in psutil.process_iter(["name", "exe"]):
            try:
                name = (process.info.get("name") or "").lower()
                executable = process.info.get("exe")
                if not executable or "unrealeditor" not in name:
                    continue
                candidate = _remote_execution_from_editor(Path(executable))
                if candidate is not None:
                    candidates.append(candidate)
            except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
                continue
    return candidates


def load_remote_execution(
    *,
    editor_executable: str | Path | None = None,
    allow_process_discovery: bool = False,
) -> ModuleType:
    """Load Unreal's helper, preferring an explicitly selected copy."""
    for path in _candidate_module_paths(
        editor_executable=editor_executable,
        allow_process_discovery=allow_process_discovery,
    ):
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
            "Could not find Unreal's remote_execution.py. Supply "
            "--unreal-exe, set UNREAL_EDITOR_EXE/UNREAL_ENGINE_ROOT/"
            "UNREAL_REMOTE_EXECUTION_PATH, or explicitly allow running-process "
            "discovery with --discover."
        ) from exc


class UnrealRemoteBackend:
    """Discover an Unreal node and execute one command at a time."""

    def __init__(
        self,
        *,
        editor_executable: str | Path | None = None,
        allow_process_discovery: bool = False,
    ) -> None:
        self._lock = threading.Lock()
        self.editor_executable = editor_executable
        self.allow_process_discovery = allow_process_discovery

    def discover(self, wait_seconds: float = 1.5) -> list[dict[str, Any]]:
        module = self._load_remote_execution()
        remote = module.RemoteExecution()
        remote.start()
        try:
            return [dict(node) for node in self._wait_for_nodes(remote, wait_seconds)]
        finally:
            remote.stop()

    def execute(
        self,
        command: str,
        *,
        node_id: str | None = None,
        wait_seconds: float = 2.0,
    ) -> dict[str, Any]:
        """Execute Python in Unreal's embedded interpreter."""
        with self._lock:
            module = self._load_remote_execution()
            remote = module.RemoteExecution()
            remote.start()
            try:
                nodes = self._wait_for_nodes(remote, wait_seconds)
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

    def _load_remote_execution(self) -> ModuleType:
        return load_remote_execution(
            editor_executable=self.editor_executable,
            allow_process_discovery=self.allow_process_discovery,
        )

    @staticmethod
    def _wait_for_nodes(remote: Any, wait_seconds: float) -> list[dict[str, Any]]:
        deadline = time.monotonic() + max(0.0, wait_seconds)
        nodes = list(remote.remote_nodes)
        while not nodes and time.monotonic() < deadline:
            time.sleep(0.1)
            nodes = list(remote.remote_nodes)
        return nodes
