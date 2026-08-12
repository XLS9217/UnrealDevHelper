"""Direct command-line adapter for UnrealApplication."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .application import UnrealApplication
from .backend import UnrealRemoteBackend


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="unreal-dev-helper")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--unreal-exe", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)

    discover = commands.add_parser("discover", help="discover the open Unreal Editor")
    discover.add_argument("--wait", type=float, default=1.5)

    execute = commands.add_parser("execute-python", help="run read-only Python in Unreal")
    source = execute.add_mutually_exclusive_group(required=True)
    source.add_argument("--code")
    source.add_argument("--file", type=Path)

    inspect = commands.add_parser("inspect-uasset", help="inspect one Unreal asset")
    inspect.add_argument("asset_path")
    inspect.add_argument("--node", default="/")
    inspect.add_argument("--detail", action="store_true")
    return parser


def _write(payload: dict, *, compact: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if compact else 2))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    application = UnrealApplication(
        UnrealRemoteBackend(editor_executable=args.unreal_exe)
    )

    try:
        if args.command == "discover":
            data = application.discover(args.wait)
        elif args.command == "execute-python":
            code = args.code if args.file is None else args.file.read_text(encoding="utf-8")
            data = application.execute_python(code)
        elif args.command == "inspect-uasset":
            # Agent-facing CLI intentionally exposes only the concise schema.
            if args.detail:
                data = application.inspect_uasset_detail(
                    args.asset_path, node=args.node, full=False
                )
            else:
                data = application.inspect_uasset_outline(
                    args.asset_path, node=args.node
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
