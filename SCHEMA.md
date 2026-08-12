# Inspection schema

`UnrealApplication.inspect_uasset_outline(asset_path, node="/")` traverses one asset without returning actual values. `UnrealApplication.inspect_uasset_detail(asset_path, node="/", full=False)` returns the selected subtree with actual values.

- `full=False` is the agent-facing form. Empty strings, empty arrays, empty objects, `null`, and `false` fields are omitted recursively.
- `full=True` is the human-facing form. Every field defined below is emitted, including empty and false values.
- Numbers, including zero, are never filtered because zero may be meaningful.
- The CLI exposes outline and filtered detail. It intentionally has no full-output option.

## Python result envelope

```json
{
  "asset_path": "string",
  "inspection": {}
}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `asset_path` | string | Asset path requested by the caller. |
| `inspection` | Inspection success or error | Native plugin response. |

## Inspection success

```json
{
  "schema_version": 1,
  "ok": true,
  "data": {}
}
```

`data` is exactly one of `Blueprint`, `BehaviorTree`, `Blackboard`, or `EnvironmentQuery`.

## Inspection error

```json
{
  "schema_version": 1,
  "ok": false,
  "error": {
    "code": "string",
    "message": "string",
    "asset_path": "string"
  }
}
```

Known error codes are `invalid_asset_path`, `asset_not_found`, and `unsupported_asset_type`. The Python bridge can also return `invalid_plugin_response` if native output is not valid JSON.

## Blueprint

```text
Blueprint {
  asset_path: string
  class: string
  name: string
  parent_class: string
  generated_class: string
  interfaces: string[]
  variables: BlueprintVariable[]
  components: BlueprintComponent[]
  graphs: BlueprintGraph[]
}

BlueprintVariable {
  name: string
  id: string
  type: PinType
  default_value: string
}

BlueprintComponent {
  name: string
  id: string
  component_class: string
  template: string
  children: string[]
}

BlueprintGraph {
  name: string
  id: string
  kind: "event" | "function" | "macro" | "delegate"
  schema: string
  nodes: BlueprintNode[]
}

BlueprintNode {
  id: string
  class: string
  title: string
  comment: string
  x: number
  y: number
  operation?: CallFunctionOperation | VariableOperation
  pins: BlueprintPin[]
}

CallFunctionOperation {
  kind: "call_function"
  function: string
  owner: string
}

VariableOperation {
  kind: "variable"
  variable: string
}

BlueprintPin {
  id: string
  name: string
  direction: "input" | "output"
  type: PinType
  default_value: string
  default_object: string
  default_text: string
  hidden: boolean
  orphaned: boolean
  links: PinLink[]
}

PinType {
  category: string
  subcategory: string
  subcategory_object: string
  container: "none" | "array" | "set" | "map"
  is_reference: boolean
  is_const: boolean
}

PinLink {
  pin_id: string
  node_id: string
}
```

`operation` exists only for recognized call-function and variable nodes. A link's `node_id` is empty in full mode if its owning node cannot be resolved.

## Behavior Tree

```text
BehaviorTree {
  asset_path: string
  class: string
  blackboard: string
  root_decorators: BehaviorTreeNodeSummary[]
  root: BehaviorTreeNode | null
}

BehaviorTreeNodeSummary {
  name: string
  class: string
  description: string
}

BehaviorTreeNode {
  name: string
  class: string
  description: string
  kind?: "composite" | "task"
  services?: BehaviorTreeNodeSummary[]
  children?: BehaviorTreeChild[]
}

BehaviorTreeChild {
  decorators: BehaviorTreeNodeSummary[]
  node: BehaviorTreeNode
}
```

`kind`, `services`, and `children` are structurally conditional even in full mode: composite nodes have `kind`, `services`, and `children`; task nodes have `kind` and `services`; other node classes contain only the summary fields.

## Blackboard

```text
Blackboard {
  asset_path: string
  class: string
  parent: string
  has_synchronized_keys: boolean
  keys: BlackboardKey[]
}

BlackboardKey {
  name: string
  description: string
  category: string
  instance_synced: boolean
  key_type: string
  key_type_class: string
}
```

## Environment Query

```text
EnvironmentQuery {
  asset_path: string
  class: string
  query_name: string
  options: EnvironmentQueryOption[]
}

EnvironmentQueryOption {
  title: string
  details: string
  generator?: EnvironmentQueryNode
  tests: EnvironmentQueryNode[]
}

EnvironmentQueryNode {
  class: string
  title: string
  details: string
}
```

`generator` is structurally conditional and exists only when the option has a generator.

## Full versus partial example

Full:

```json
{
  "description": "",
  "instance_synced": false,
  "category": "Gameplay",
  "children": []
}
```

Partial:

```json
{
  "category": "Gameplay"
}
```
