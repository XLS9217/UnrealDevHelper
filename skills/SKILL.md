---
name: unreal-dev-helper
description: Connect to one open Unreal Editor and inspect supported Unreal assets through the UnrealDevHelper Python CLI and native editor plugin. Use for project setup, Editor discovery, read-only Unreal Python, or traversing Blueprint, Behavior Tree, Blackboard, and Environment Query assets by outline and detail nodes. Never use inspection Python to modify Unreal content.
---

# Unreal Dev Helper

Use this project as a read-only bridge to one running Unreal Editor. The native editor plugin reads Unreal objects; the local Python application transports requests and converts native Blueprint graphs into concise agent-facing logic.

Read only the reference needed for the task:

- Read [references/project-usage.md](references/project-usage.md) to set up the repository, connect to Unreal, discover the Editor, or run commands.
- Read [references/viewing-uassets.md](references/viewing-uassets.md) before inspecting or explaining a `.uasset`.

Always inspect progressively: request an outline, select a node, then request that node's detail. Treat `inspection.ok: false` as a failed operation and report the native error.

Treat every inspection response as a useful representation, not a complete serialization of the `.uasset`. Support evolves one asset type and section at a time, so an omitted property does not prove that the property is absent in Unreal. If a missing, misleading, or ambiguous representation prevents a confident answer, compare partial and full detail when available, then record the evidence in the repository-root `REPRESENTATION_ISSUES.md`. Do not silently invent missing data or speculative fixes.

For every graph-like asset or section, stop outline traversal at the terminal graph and request the whole graph as detail. When extending this project for a new uasset, implement that whole-graph contract first. Never add graph-node traversal or semantic graph parsing unless the user explicitly requests it after reviewing the complete graph output. The agent must see the same graph the developer sees in the Editor.

Keep `execute-python` read-only. Never use it to create, edit, compile, rename, move, delete, or save assets; spawn or destroy objects; change properties; or run mutating console commands. Add future writes only as explicit reviewed application operations backed by fixed scripts.
