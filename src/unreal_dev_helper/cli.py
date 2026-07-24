"""Command-line frontend for Unreal Dev Helper."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import sys
from typing import Any, Sequence

from .application import UnrealApplication
from .backend import UnrealRemoteBackend
from .server import BACKEND_HOST, BACKEND_PORT, serve


def _request(operation: str, params: dict[str, Any] | None = None) -> Any:
    payload = json.dumps(
        {"operation": operation, "params": params or {}},
        ensure_ascii=False,
    ).encode("utf-8") + b"\n"
    try:
        with socket.create_connection((BACKEND_HOST, BACKEND_PORT), timeout=10) as connection:
            connection.sendall(payload)
            response = json.loads(connection.makefile("rb").readline().decode("utf-8"))
    except OSError as exc:
        raise RuntimeError(
            "The Unreal Dev Helper backend is not running. Start it in a "
            "terminal with: uv run unreal-dev-helper backend"
        ) from exc
    if not response.get("ok"):
        error = response.get("error") or {}
        raise RuntimeError(f"{error.get('type', 'BackendError')}: {error.get('message', '')}")
    return response.get("data")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="unreal-dev-helper",
        description="Use one machine-local backend to inspect Unreal Editor.",
    )
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--unreal-exe", type=Path)
    parser.add_argument("--discover", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("backend", help="run the unique backend in this terminal")
    subparsers.add_parser("backend-status", help="check whether the backend is running")

    status = subparsers.add_parser("status", help="discover Unreal Editor nodes")
    status.add_argument("--wait", type=float, default=1.5)

    execute = subparsers.add_parser(
        "execute-python",
        help="run a read-only Python inspection query",
    )
    source = execute.add_mutually_exclusive_group(required=True)
    source.add_argument("--code")
    source.add_argument("--file", type=Path)
    execute.add_argument("--node")

    blueprint = subparsers.add_parser(
        "blueprint-info",
        help="read a Blueprint class default object",
    )
    blueprint.add_argument("asset_path")
    blueprint.add_argument("--include-private", action="store_true")
    blueprint.add_argument("--max-depth", type=int, default=3)
    blueprint.add_argument("--max-items", type=int, default=128)
    blueprint.add_argument("--node")
    return parser


def _write(payload: dict[str, Any], *, compact: bool) -> None:
    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=None if compact else 2,
            default=str,
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "backend":
        application = UnrealApplication(
            UnrealRemoteBackend(
                editor_executable=args.unreal_exe,
                allow_process_discovery=args.discover,
            )
        )
        try:
            serve(application)
        except KeyboardInterrupt:
            pass
        except Exception as exc:
            _write(
                {
                    "ok": False,
                    "command": args.command,
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                },
                compact=args.compact,
            )
            return 1
        return 0

    try:
        if args.command == "backend-status":
            data = _request("health")
        elif args.command == "status":
            data = _request("status", {"wait_seconds": args.wait})
        elif args.command == "execute-python":
            code = args.code
            if args.file is not None:
                code = args.file.read_text(encoding="utf-8")
            data = _request(
                "execute_python",
                {"code": code, "node_id": args.node},
            )
        elif args.command == "blueprint-info":
            data = _request(
                "blueprint_info",
                {
                    "asset_path": args.asset_path,
                    "include_private": args.include_private,
                    "max_depth": args.max_depth,
                    "max_items": args.max_items,
                    "node_id": args.node,
                },
            )
        else:  # pragma: no cover
            raise ValueError(f"Unknown command: {args.command}")
    except Exception as exc:
        _write(
            {
                "ok": False,
                "command": args.command,
                "error": {"type": type(exc).__name__, "message": str(exc)},
            },
            compact=args.compact,
        )
        return 1

    _write({"ok": True, "command": args.command, "data": data}, compact=args.compact)
    return 0


if __name__ == "__main__":
    sys.exit(main())
