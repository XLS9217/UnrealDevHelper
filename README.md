# Unreal Dev Helper

Unreal Dev Helper lets a code agent inspect Unreal assets through two parts:

- `UnrealDevHelperPlugin` is an editor-only Unreal plugin. Unreal loads the assets in their real project context, and the plugin exposes read-only Blueprint structure as JSON.
- The Python CLI connects directly to the single open Unreal Editor through Python Remote Execution and calls the plugin inside that Editor process.

The plugin exposes one inspection call: `unreal.UnrealDevHelperLibrary.inspect_uasset(asset_path)`. The library routes Blueprint, Behavior Tree, Blackboard, and Environment Query assets to their native inspectors. It does not modify or save assets.

# How to use

Copy the complete `UnrealDevHelperPlugin` directory into the target project's `Plugins` directory:

```text
MyGame/
|-- MyGame.uproject
`-- Plugins/
    `-- UnrealDevHelperPlugin/
        |-- UnrealDevHelperPlugin.uplugin
        `-- Source/
```

Enable `UnrealDevHelperPlugin` and `PythonScriptPlugin` for the project. In **Project Settings > Plugins > Python**, enable Remote Execution. Regenerate project files or build the project's Editor target, then open the `.uproject`. The plugin is editor-only and is not included in packaged game targets.

Find the Unreal Engine root directory. This is the directory that contains the `Engine` folder, not the `Engine` folder itself. For example, if the Editor executable is `E:\Apps\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe`, the engine root is `E:\Apps\UE_5.7`. The following file must exist beneath it:

```text
Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py
```

Copy `.env.example` to `.env` and enter that root:

```dotenv
UNREAL_ENGINE_ROOT=E:\Apps\UE_5.7
```

`.env` is machine-local and ignored by Git. Environment variables already set in the terminal take precedence over values in `.env`.

Install the Python dependencies from this repository:

```powershell
uv sync
```

Discover the open Unreal project and verify that the plugin is loaded:

```powershell
uv run unreal-dev-helper discover

uv run unreal-dev-helper execute-python `
  --code "import unreal; print(unreal.UnrealDevHelperLibrary.ping())"
```

Inspect a Blueprint by its Unreal asset path:

```powershell
uv run unreal-dev-helper inspect-uasset /Game/Path/BP_Name
```

`inspect-uasset` always executes the reviewed `unreal_scripts/inspect_uasset.py` file. The CLI assumes only one Unreal Editor instance is open. Keep `execute-python` read-only; future integrations such as MCP can call the same three `UnrealApplication` methods.
