# Using the project

## Architecture

Unreal Dev Helper has two cooperating parts:

```text
CLI / UnrealApplication
→ Python Remote Execution
→ open Unreal Editor
→ UnrealDevHelperPlugin
→ project assets loaded in their real Unreal context
```

The Python command does not start an Editor. Exactly one target Unreal Editor should already be open with the intended game project and plugin loaded.

## Required setup

1. Work from the UnrealDevHelper repository root.
2. Read `.env`. If missing, copy `.env.example` to `.env`.
3. Set `UNREAL_ENGINE_ROOT` to the directory containing `Engine`, not to `Engine` itself.
4. Confirm this file exists:

   ```text
   <UNREAL_ENGINE_ROOT>/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py
   ```

5. Run `uv sync` if the local Python environment is not prepared.
6. Confirm the target game project contains and enables:
   - `UnrealDevHelperPlugin`
   - `PythonScriptPlugin`
7. In Unreal, enable Python Remote Execution under Project Settings > Plugins > Python.
8. Build the game's Editor target after native plugin changes, then open the `.uproject`.

Do not search the user's filesystem for an unknown Engine location without permission. Ask for the Engine root when it cannot be determined from repository configuration.

## Verify the connection

Discover the one open Editor:

```powershell
uv run unreal-dev-helper discover
```

Verify the plugin when needed:

```powershell
uv run unreal-dev-helper execute-python --code "import unreal; print(unreal.UnrealDevHelperLibrary.ping())"
```

If a newly added native method is missing, the open Editor is using an older DLL. Close the Editor, rebuild the Editor target, and reopen the project.

## CLI commands

```powershell
uv run unreal-dev-helper discover
uv run unreal-dev-helper inspect-uasset /Game/Path/BP_Name
uv run unreal-dev-helper inspect-uasset /Game/Path/BP_Name --node /graphs
uv run unreal-dev-helper inspect-uasset /Game/Path/BP_Name --node /graphs/EventGraph --detail
uv run unreal-dev-helper execute-python --code "import unreal; unreal.log('read-only check')"
```

`inspect-uasset` defaults to an outline. Add `--detail` only after choosing the node whose values are needed. The agent-facing CLI always returns filtered/parsed detail and intentionally provides no full-output flag.

## Application API

Use the application directly for integrations or human comparison scripts:

```python
from src.application import UnrealApplication

app = UnrealApplication()
outline = app.inspect_uasset_outline(asset_path, node="/")
parsed = app.inspect_uasset_detail(asset_path, node="/graphs", full=False)
native = app.inspect_uasset_detail(asset_path, node="/graphs", full=True)
```

- `full=False`: agent-facing filtered or semantically parsed result.
- `full=True`: human/debug native result for the selected node.

See the repository `SCHEMA.md` when exact response fields are required.

## Safety

Use `execute-python` only for read-only investigation. Do not mutate assets or Editor state through arbitrary Python. Inspection APIs themselves are read-only and do not save packages.
