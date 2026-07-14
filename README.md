# Unreal Dev Helper

A stdio MCP server for running Python inside Unreal Editor through Remote
Execution. Editor-side code can use `import unreal`.

## Setup

1. Enable Unreal's **Python Editor Script Plugin**.
2. Enable **Project Settings > Plugins > Python > Remote Execution**.
3. Install dependencies:

```powershell
uv sync
```

Register the server with Codex using the repository's absolute path:

```powershell
codex mcp add unreal -- uv run --directory E:\Project\_TAG\UnrealDevHelper python src/mcp/server.py
```

Restart Codex after registering or changing files under `src/mcp`.

## Layout

- `src/mcp`: stdio MCP server and Unreal connection code.
- `unreal_scripts`: Python scripts executed inside Unreal Editor.

The server finds Unreal's `remote_execution.py` from the running
`UnrealEditor` process. No engine installation path is required.

## Tools

- `unreal_status`: find running Unreal Editor nodes.
- `unreal_execute_python`: execute trusted Python inside the Editor.
- `blueprint_info`: read a Blueprint class default object.

Remote Execution can run arbitrary Python. Use it only on a trusted development
machine and network.
