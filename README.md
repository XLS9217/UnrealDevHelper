# Unreal Dev Helper

An stdio MCP server that lets a code agent run Python inside a running Unreal
Editor through Unreal's Python Remote Execution protocol. Code sent through the
server runs in Unreal's embedded interpreter, so `import unreal` is available.

## Layout

- `src/unrealdevhelper` contains the MCP server and remote-execution adapter.
- `unreal_scripts` contains scripts executed inside Unreal Editor.
- `unreal_scripts/blueprint_info.py` reads a Blueprint generated class's class
  default object (CDO) and returns its editor-visible properties.

## Unreal setup

1. Enable the **Python Editor Script Plugin**.
2. In **Project Settings > Plugins > Python**, enable Remote Execution.
3. Keep the project open in Unreal Editor while using the MCP tools.
The server automatically derives the location of Unreal's bundled
`remote_execution.py` from the running `UnrealEditor` process. No engine
installation path is required. The helper is normally located at:

   ```text
   <UE_ROOT>/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py
   ```

For unusual source builds or renamed editor executables, `UNREAL_ENGINE_ROOT`
or `UNREAL_REMOTE_EXECUTION_PATH` can be supplied as an optional override.
Using the helper shipped by the running Unreal version avoids protocol
mismatches.

## Run and register

Install the project:

```powershell
uv sync
```

Register it with Codex using only the absolute repository path:

```powershell
codex mcp add unreal `
  -- uv run --directory E:\Project\_TAG\UnrealDevHelper unrealdevhelper-mcp
```

Restart or reload Codex after registering the server. The MCP server writes only
protocol messages to stdout; SDK diagnostics and errors use stderr.

## Tools

- `unreal_status`: discover running Unreal Editor nodes.
- `unreal_execute_python`: execute trusted Python in the editor.
- `blueprint_info`: read the generated class and CDO properties for a Blueprint
  path such as `/Game/Blueprints/BP_Player`.

If multiple editors are discovered, pass a node ID returned by
`unreal_status`, or set `UNREAL_REMOTE_NODE_ID` for the server process.

Remote execution permits arbitrary Python inside the editor. Only run this MCP
server and Unreal Remote Execution on a trusted development machine/network.
