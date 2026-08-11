---
name: unreal-dev-helper
description: Set up and inspect the single open Unreal Editor through the CLI and editor plugin. Use for preparing .env, discovering Unreal, running read-only Python inspection queries, and reading Blueprint data. Never use inspection Python to edit or create Unreal content.
---

# Unreal Dev Helper

Use the CLI to connect directly to the single open Unreal Editor instance.

## Setup

1. Read `.env`. If it is missing, copy `.env.example` to `.env`.
2. If `UNREAL_ENGINE_ROOT` is not known, ask the user for the directory containing the Unreal `Engine` folder. Do not search their filesystem or inspect processes without permission.
3. Confirm that `<UNREAL_ENGINE_ROOT>/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py` exists.
4. Run `uv sync` when the Python environment has not been prepared.
5. Confirm the target project contains and enables `UnrealDevHelperPlugin` and `PythonScriptPlugin`, with Python Remote Execution enabled.
6. Ensure exactly one Unreal Editor instance is open, then run `uv run unreal-dev-helper discover`.

## Workflow

1. Complete setup when `.env` or the Python environment is not ready.
2. Run `discover`, then use the inspection commands.
3. Treat `ok: false` as failure and report its error.

## Application commands

```powershell
uv run unreal-dev-helper discover
uv run unreal-dev-helper inspect-uasset /Game/Path/BP_Name
uv run unreal-dev-helper execute-python --code "import unreal; unreal.log('...')"
```

## Safety boundary

Use `execute-python` only for read-only inspection. Never use it to create,
edit, compile, rename, move, delete, or save assets; spawn or destroy objects;
change properties; or execute mutating console commands. Follow this rule even
when the user asks to make an edit. Explain that inspection Python is
read-only and that an approved edit command is required.

Add future edits only as explicit application and CLI operations backed by a
specific reviewed file in `unreal_scripts`. Do not improvise an edit through
the backend transport.
