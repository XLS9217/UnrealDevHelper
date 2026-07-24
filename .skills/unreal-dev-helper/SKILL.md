---
name: unreal-dev-helper
description: Inspect a running Unreal Editor through the project's machine-local backend and CLI. Use for checking the shared backend, discovering Unreal nodes, running read-only Python inspection queries, and reading Blueprint class default objects. Never use inspection Python to edit or create Unreal content.
---

# Unreal Dev Helper

Use one backend terminal per computer. All agents share it through the CLI.

## Workflow

1. Check whether the backend already exists:

   ```powershell
   uv run unreal-dev-helper backend-status
   ```

2. If it is running, continue to the application commands.
3. If it is absent, ask the user for either:
   - The full path to `UnrealEditor.exe`; or
   - Permission to inspect running processes.
4. Start the backend in a terminal and leave it running:

   ```powershell
   uv run unreal-dev-helper --unreal-exe "E:\Path\UnrealEditor.exe" backend
   ```

   With explicit discovery permission:

   ```powershell
   uv run unreal-dev-helper --discover backend
   ```

5. Run `status`, then use `--node` when multiple Unreal nodes exist.
6. Treat `ok: false` as failure and report its error.

Do not inspect processes or search for Unreal without permission. Do not start
a second backend when `backend-status` succeeds.

## Application commands

```powershell
uv run unreal-dev-helper status
uv run unreal-dev-helper blueprint-info /Game/Path/BP_Name
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
