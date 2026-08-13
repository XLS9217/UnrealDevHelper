# Representation issues

Record limitations discovered while inspecting real assets. An omitted field does not prove that the value is absent in Unreal. Compare partial and full detail when possible, and record evidence rather than speculation.

## Open

### Inherited Blueprint component templates are not exposed

- Asset type: Blueprint
- Asset path: `/Game/TheAgentGame/BP_AgenticCharacter`
- Requested node: `/components`
- Missing, misleading, or ambiguous representation: The outline reports zero components and component detail falls back to Blueprint identity, although the inherited `ACharacter` CDO contains `CharacterMesh0`, `CharacterMovement`, and `CapsuleComponent` templates.
- Why it matters: An agent cannot determine the character's skeletal mesh, animation mode, or Anim Blueprint through the normal progressive inspector.
- Partial/full or Editor evidence: Read-only Unreal CDO reflection reports mesh `/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple`, animation mode `Animation Blueprint`, and animation class `/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed`.
- Suggested next investigation: Include inherited native component templates in the Blueprint component outline and detail representation.

<!--
### Short problem name

- Asset type:
- Asset path:
- Requested node:
- Missing, misleading, or ambiguous representation:
- Why it matters:
- Partial/full or Editor evidence:
- Suggested next investigation:
-->

## Resolved

Move an entry here when its representation or documentation has been corrected.
