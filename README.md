# Unreal Dev Helper

A small CLI with one shared backend process for Unreal Editor Remote Execution.
The backend runs in a terminal and application commands connect to it over
localhost.

## Setup

1. Enable Unreal's **Python Editor Script Plugin**.
2. Enable **Project Settings > Plugins > Python > Remote Execution**.
3. Install dependencies:

```powershell
uv sync
```

## Start the backend

Check whether another terminal or agent already started it:

```powershell
uv run unreal-dev-helper backend-status
```

If absent, start one backend and leave its terminal running:

```powershell
uv run unreal-dev-helper `
  --unreal-exe "E:\Apps\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe" `
  backend
```

Alternatively, after explicitly authorizing process discovery:

```powershell
uv run unreal-dev-helper --discover backend
```

The fixed localhost port permits only one backend on the computer.

## Application CLI

```powershell
uv run unreal-dev-helper status
uv run unreal-dev-helper blueprint-info /Game/Path/BP_Name
uv run unreal-dev-helper execute-python --code "import unreal; unreal.log('...')"
```

The CLI returns a stable JSON envelope. `execute-python` is intended only for
read-only inspection by code agents.

## Architecture

- `.skills/unreal-dev-helper`: workflow and safety rules for code agents.
- `src/unreal_dev_helper/cli.py`: terminal and application CLI.
- `src/unreal_dev_helper/server.py`: shared localhost backend.
- `src/unreal_dev_helper/application.py`: allowlisted operations.
- `src/unreal_dev_helper/backend.py`: Unreal node connection.
- `unreal_scripts`: reviewed scripts used by explicit operations.

Agents must never use inspection Python to create or edit Unreal content, even
when asked. Future edits must be implemented as explicit commands backed by a
related reviewed script in `unreal_scripts`.
