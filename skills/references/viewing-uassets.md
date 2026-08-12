# Viewing uassets

## Mental model

Treat one `.uasset` as a virtual tree. `asset_path` always selects one file; `node` selects a location inside its inspection tree.

This virtual tree is an intentionally incomplete inspection representation, not a lossless decode of the asset. Inspectors expose the information currently selected for agent use, and coverage evolves type by type. Missing output therefore means "not represented" unless native evidence proves the value is absent.

Two operations exist:

- `outline`: return only the selected node's immediate children and navigation metadata.
- `detail`: return actual values for the selected node and its subtree.

Use this sequence:

```text
root outline
→ section outline
→ selected section detail
→ deeper detail only when needed
```

Do not request root detail merely to learn what the file contains.

If the representation prevents a confident answer:

1. Compare partial detail with `full=True` detail when available.
2. Describe only what the returned evidence establishes.
3. Add the discovered gap to the repository-root `REPRESENTATION_ISSUES.md` using its template.

Record problems found while inspecting real assets. Do not add hypothetical limitations, and do not expand an inspector or introduce graph parsing unless the user asks after reviewing the evidence.

## Required rule for new graph-like assets

When inspecting or implementing support for a new graph-like uasset, expose its graph as one terminal outline child and return the complete graph from detail. Do not recursively expose graph nodes, pins, tests, transitions, or branches through outline. Do not introduce a secondary parser until the user has compared the complete returned graph with the Unreal Editor view and explicitly asks for parsing.

The governing principle is: **the agent sees what the developer sees, so they are on the same page.**

## Basic traversal

Start at the root:

```powershell
uv run unreal-dev-helper inspect-uasset /Game/TheAgentGame/BP_AgenticCharacter
```

A Blueprint root can expose nodes such as:

```text
/
├── identity
├── class_defaults
├── components
├── variables
├── interfaces
└── graphs
```

Expand a section's outline:

```powershell
uv run unreal-dev-helper inspect-uasset /Game/TheAgentGame/BP_AgenticCharacter --node /class_defaults
uv run unreal-dev-helper inspect-uasset /Game/TheAgentGame/BP_AgenticCharacter --node /graphs
```

Read selected values:

```powershell
uv run unreal-dev-helper inspect-uasset /Game/TheAgentGame/BP_AgenticCharacter --node /class_defaults --detail
uv run unreal-dev-helper inspect-uasset /Game/TheAgentGame/BP_AgenticCharacter --node /graphs/EventGraph --detail
```

## Blueprint behavior

### Class defaults

Class defaults come from the generated class's Class Default Object (CDO).

- Parsed detail returns editable values changed from the parent CDO.
- Full detail includes inherited editable values as well.
- Outline `/class_defaults` lists property categories.
- Outline a category to list its properties; request category detail to read its values.

Class defaults are separate from component template values and graph pin defaults.

### Graphs

Graph entries returned by outline `/graphs` are terminal: they are detail-addressable but not outline-expandable. Request graph detail directly.

C++ returns the selected graph's complete native nodes, pins, defaults, and links. For `full=False`, Python's `src/util/graph_parse.py` converts that native structure into concise logic:

```json
{
  "nodes": [
    {"id": "n1", "name": "Event BeginPlay", "kind": "event"},
    {"id": "n2", "name": "Print String", "kind": "call_function"}
  ],
  "connections": [
    {"from": "n1.then", "to": "n2.execute"}
  ]
}
```

Parsed graphs omit disconnected nodes, unused pins, GUIDs, coordinates, schemas, hidden self pins, repeated type blocks, and reciprocal duplicate links. They retain connected logic, function/variable identity, and authored unconnected input values. Use `full=True` only when raw native pin data is genuinely needed.

### Components and variables

Use their section outlines to discover names, then request section detail. Blueprint optimization is evolving type by type; do not assume every terminal child already supports individual detail.

## Blackboard

```text
/
├── identity
├── parent
└── keys
    └── <key-name>
```

Outline `/keys` to discover key names. Request `/keys/<key-name>` detail for one key or `/keys` detail for all keys.

## Behavior Tree

```text
/
├── identity
├── blackboard
└── tree
    └── root
        └── <child-index>
```

The Behavior Tree outline stops at terminal `/graph`. Request `/graph` detail to receive the entire native recursive tree, including decorators and services. It is intentionally not parsed or optimized yet so the agent sees the same complete structure shown in the Behavior Tree editor.

## Environment Query

```text
/
├── identity
└── options
    └── <option-index>
        ├── generator
        └── tests
            └── <test-index>
```

The Environment Query outline stops at terminal `/graph`. Request `/graph` detail to receive every option with its generator and tests. It is intentionally not parsed or optimized yet so the agent sees the same complete structure shown in the EQS editor.

These three inspectors currently return their native filtered structure directly. Do not invent a generic Unreal Python fallback when a native traversal path fails.

## Understanding responses

Python wraps the native result:

```json
{
  "asset_path": "/Game/Path/Asset",
  "inspection": {
    "schema_version": 1,
    "ok": true,
    "data": {}
  }
}
```

On failure, inspect `inspection.error.code` and `inspection.error.message`. Common causes:

- `asset_not_found`: wrong `/Game/...` path or asset unavailable in the open project.
- `unsupported_asset_type`: no inspector exists for that asset class.
- `invalid_inspection_node`: the virtual node does not exist or is terminal.
- `outline_not_implemented`: that asset type does not yet implement progressive outline traversal.
- Missing Python-exposed method: rebuild and restart Unreal to load the new plugin DLL.

Never substitute generic Unreal Python reflection when the purpose is to test native plugin support; report the native limitation clearly.
