"""Small machine-local backend server."""

from __future__ import annotations

import json
import socketserver
from typing import Any

from .application import UnrealApplication


BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 47651


def dispatch_request(
    request: dict[str, Any],
    application: UnrealApplication,
) -> dict[str, Any]:
    """Dispatch an allowlisted application operation."""
    operation = request.get("operation")
    params = request.get("params") or {}
    if not isinstance(params, dict):
        raise ValueError("Request params must be an object.")

    if operation == "health":
        return {"ready": True}
    if operation == "status":
        return application.status(wait_seconds=float(params.get("wait_seconds", 1.5)))
    if operation == "execute_python":
        return application.execute_python(
            str(params["code"]),
            node_id=params.get("node_id"),
        )
    if operation == "blueprint_info":
        return application.blueprint_info(
            str(params["asset_path"]),
            include_private=bool(params.get("include_private", False)),
            max_depth=int(params.get("max_depth", 3)),
            max_items=int(params.get("max_items", 128)),
            node_id=params.get("node_id"),
        )
    raise ValueError(f"Unknown or disallowed operation: {operation!r}")


class BackendServer(socketserver.ThreadingTCPServer):
    daemon_threads = True

    def __init__(self, application: UnrealApplication) -> None:
        self.application = application
        super().__init__((BACKEND_HOST, BACKEND_PORT), RequestHandler)


class RequestHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            request = json.loads(self.rfile.readline(1024 * 1024).decode("utf-8"))
            data = dispatch_request(request, self.server.application)
            response = {"ok": True, "data": data}
        except Exception as exc:
            response = {
                "ok": False,
                "error": {"type": type(exc).__name__, "message": str(exc)},
            }
        self.wfile.write(
            json.dumps(response, ensure_ascii=False, default=str).encode("utf-8")
            + b"\n"
        )


def serve(application: UnrealApplication) -> None:
    """Run the one backend allowed on this computer."""
    try:
        with BackendServer(application) as server:
            print(f"Unreal Dev Helper backend listening on {BACKEND_HOST}:{BACKEND_PORT}")
            server.serve_forever()
    except OSError as exc:
        raise RuntimeError(
            f"A backend is already using {BACKEND_HOST}:{BACKEND_PORT}."
        ) from exc
