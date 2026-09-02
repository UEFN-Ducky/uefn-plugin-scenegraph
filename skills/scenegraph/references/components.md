---
description: "Full Scene Graph builtin component catalog — mesh/asset vs plain, BasicShapes, lights (one per entity), KFM, interactable (no button_component), itemization components, project Verse class paths"
metadata:
  order: 3
  label: "Component catalog"
  default_enabled: false
  load_condition: "Attaching or explaining entity components, mesh/light/sound/particle assets, interactables, keyframed movement, or project Verse component class paths"
---

## Scene Graph component catalog

Always probe the live build first:

```
scene_graph_capabilities({})
unreal__describe_toolset({"toolset_name": "ValkyrieToolset.EntityToolset"})   # component/class listing + AddComponent live here
```

Kinds reported by the EntityToolset component listing:

| Kind | Meaning |
|------|---------|
| `builtin` | Engine aliases (`mesh_component`, …) |
| `project` | Your Verse `*_component` classes after Verse build |
| `asset_generated` | Digest classes for project meshes/particles/sounds |

**One component per subclass _group_**, not per class — re-adding returns the
existing one. The digest's own example is lights: `spot_`, `sphere_`, `rect_`,
`capsule_` and `directional_light_component` all derive from `light_component`,
so an entity can hold **one light in total**. Two lights = two entities.

**Property names** are case-sensitive Verse digest names (`Visible`, `Collidable`).
Check with `get_verse_api({"name": "<component>"})`. Never pass mangled
`__verse_0x...` names to tools.

There is **no** Scene Graph `button_component`. Player interaction uses
`interactable_component` / `basic_interactable_component`. Creative
`button_device` is a **device**, not an entity component — wire it with device
tools, not Scene Graph.

---

### Plain vs asset components

| Kind | Examples | `asset_path` |
|------|----------|--------------|
| **Plain** | transform, mass, lights, KFM, interactable, camera, … | Omit |
| **Asset** | mesh, particle, sound | **Required** — PROJECT mount only (`/MyProject/...`). Never `/Game/...` Fortnite content |

Asset attach creates a **subclass** of the base (e.g.
`SolarSystem-Meshes-SM_Body_Earth` under `mesh_component`). Read/remove by
base alias still works.

That `asset_path` requirement is about the **editor tool**. In Verse you can
skip assets entirely for prototyping: `/UnrealEngine.com/BasicShapes` provides
`cube`, `sphere`, `plane`, `cone` and `cylinder`, each a `mesh_component`
subclass — `Ent.AddComponents(array{sphere{Entity := Ent}})`.

---

### Builtin catalog (from `scene_graph_capabilities`)

#### Pose / physics

| Alias | Role |
|-------|------|
| `transform_component` | Local/global pose. **Required** for mesh placement and any KFM/orbit pivot. Empty pivots report `local_transform_error`. Verse `SetLocalTransform` creates one on demand. |

#### Render / audio / FX (asset)

| Alias | Role |
|-------|------|
| `mesh_component` | Render mesh. Needs PROJECT `asset_path` from the editor tool (or a `BasicShapes` subclass in Verse). **Depends on `transform_component`** to be positioned at all. Digest props: `Visible`, `Collidable`, `Queryable`; it is also `enableable` (`Enable()`, `Disable()`, `IsEnabled[]`); overlap events `EntityEnteredEvent` / `EntityExitedEvent`. |
| `particle_system_component` | Particle / Niagara system — PROJECT asset. |
| `sound_component` | Sound — PROJECT asset. |

#### Motion

| Alias | Role |
|-------|------|
| `keyframed_movement_component` | Timed transform animation (orbits, doors, movers). `using { /Verse.org/SceneGraph/KeyframedMovement }`. `SetKeyframes` **rebases onto the current transform and does not autoplay** — then `Play()`. Translation/Scale on deltas are **additive** (`0` = no change). Modes: `oneshot_` / `loop_` / `pingpong_keyframed_movement_playback_mode`. `<final>` — compose, never subclass. Prefer over per-tick `SetGlobalTransform`. **Never** `creative_prop` `animation_controller` for entities. Full API: `movement_transforms`. |

#### Lights

| Alias | Role |
|-------|------|
| `light_component` | Base light |
| `spot_light_component` | Spot |
| `sphere_light_component` | Point / sphere |
| `rect_light_component` | Rect |
| `capsule_light_component` | Capsule |
| `directional_light_component` | Directional |

#### Camera / interaction / gameplay tags

| Alias | Role |
|-------|------|
| `camera_component` | Scene Graph camera |
| `interactable_component` | Player interaction surface (not a UI button) |
| `basic_interactable_component` | Simpler interactable |
| `possessable_component` | Possession |
| `icon_component` | Editor / UI icon |
| `rarity_component` | Rarity metadata — instances in `/Fortnite.com/Itemization/FortniteRarities` |
| `basic_stackable_component` | Stacking. Merge API: `CanMergeInto[]`, `MergeInto[]`, `AllowMergeInto[]`, `OnMergeInto` |

#### Itemization (`/UnrealEngine.com/Itemization`, `/Fortnite.com/Itemization`)

| Alias | Role |
|-------|------|
| `item_component` | Marks an entity as an item. `GetParentInventory[]`, `IsEquipped[]`, `Equip`, `Unequip`, `Drop[]`, `PickUp[Inventory]`, `Categories`. |
| `inventory_component` | Holds items. `AddItemDistribute` is the grant call; also `AddItem`, `RemoveItem`, `GetItems`, `FindItems`, `GetEquippedItems`, add/remove/equip events. On a player it sits on a **subentity** of the agent. |
| `fort_item_pickup_interactable_component` | World pickup. Owning entity needs `item_component` + `mesh_component`; exposes `GetInteractorInventory(Agent)`. Gated `MinUploadedAtFNVersion := 4040`. Fields from `basic_interactable_component`: `CanInteractMessage`, `CannotInteractMessage`, `Cooldown`, `CooldownPerAgent`, `SuccessLimit`, `InteractableDuration`, `Enable`/`Disable`. |
| `fort_inventory_component` (+ `fort_inventory_*` subclasses) | **Player inventory** types (weapon hotbar, resources, currencies, ammo, …) — not components for custom item prefabs. Custom items use `item_component` (+ optional `Categories`). |
| `fort_item_ability_component` | Template abilities on an item (`ItemAbilities` / `ItemEquippedAbilities`, InputTrigger, TargetQuery, AbilityElements). Digest-gated experimental. Recipes: `template_abilities`. |

#### Armory (`/Fortnite.com/Armory`)

| Alias | Role |
|-------|------|
| `fort_trace_weapon_component` | Tunable hitscan weapon (damage, fire rate, spread, recoil, magazine, FX, sounds). All have `Set*` Verse APIs — confirm with `get_verse_api`. |
| `fort_weapon_component` | Base weapon: `IsHolstered`, `HolsterChangedEvent`. |

Custom Armory Entity Prefabs (templates, mesh swap, grant/equip/clear):
`skill_read_subskill("scenegraph", "custom_weapons")`.

Custom non-weapon Entity Prefabs (pickup / description / icon / mesh, KFM spin,
equipped detect): `skill_read_subskill("scenegraph", "custom_items")`.

Template abilities (`fort_template_ability`, status-effect AbilityElements):
`skill_read_subskill("scenegraph", "template_abilities")`.

Recipes and the granting component: `skill_read_subskill("scenegraph", "itemization")`.

Digest may also expose related types (e.g. camera director) — confirm with
`get_verse_api` / `search_verse_digest` before use.

---

### Project Verse components

Custom `*_component` classes appear only **after** Verse compiles.

Resolution order in EntityToolset `AddComponent`:

1. Builtin alias (`mesh_component`, …)
2. Short Verse class name (when listed by the EntityToolset component listing (`unreal__describe_toolset` for the exact tool name))
3. Full object path — often:  
   `/<Project>/_Verse.Verse-<Module>-<class_name>`  
   Example: `/catland/_Verse.Verse-SolarOrbits-constant_rotation_component`

If short name fails, call the EntityToolset component listing (`unreal__describe_toolset` for the exact tool name) (and `reload_listener`
if the list is stale after a Verse relink) — do not invent paths and do not
walk `ObjectIterator` via `execute_python` (freezes the editor).

After EntityToolset `AddComponent`, check `class_path`. A `VERSE_DEAD_*` class under
`/Engine/Transient` is a stale VM class: `reload_listener` → destroy and
recreate the entity → attach again. Details:
`skill_read_subskill("uefn", "verse_build_lifecycle")`.

---

### Mesh attachment recipe

```
unreal__call_tool({
  "toolset_name": "ValkyrieToolset.EntityToolset",
  "tool_name": "AddComponent",
  "arguments": {"entity": "Body_Earth", "component_class": "mesh_component", "asset_path": "/MyProject/Meshes/SM_Body_Earth"}
})
# a mesh with no transform_component is not positioned at all
unreal__call_tool({"toolset_name": "ValkyrieToolset.EntityToolset", "tool_name": "AddComponent", "arguments": {"entity": "Pivot_Earth", "component_class": "transform_component"}})
# argument names: read them from unreal__describe_toolset first — never invent them
```

Put FBX axis offsets on a **child** mesh entity (`SetLocalTransform`); keep the
orbit/heading root clean for KFM yaw. Motion troubleshooting:
`skill_read_subskill("scenegraph", "movement_transforms")`.
