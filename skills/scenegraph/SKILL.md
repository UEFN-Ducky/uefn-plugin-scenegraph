---
source_plugin_id: scenegraph
name: scenegraph
description: "UEFN Scene Graph — create and edit entities, components, and prefabs in the editor via MCP tools, query the exact Verse API from digests, author Verse components that compile and actually move, grant stock items/weapons through inventories, author custom Armory weapon prefabs, custom non-weapon item prefabs, and Fortnite template abilities (fort_template_ability / fort_item_ability_component)"
license: MIT
metadata:
  label: "UEFN Scene Graph"
  version: 17
  managed_by: uefn-ducky
  author: UEFN-Ducky
  copyright: Copyright 2026 Mindful Path Company, LLC
  allow_redistribute: true
---

# UEFN Scene Graph — entities, components, prefabs

**Entity CRUD is nested Epic UEFN MCP.** Settings → MCPs → **UEFN MCP (Epic)**.
Use `unreal__list_toolsets` → `unreal__describe_toolset` → `unreal__call_tool` into
`ValkyrieToolset.EntityToolset` (`FindEntities`, `CreateEntity`, `AddComponent`,
`SetEntityTransform`, …). There are no flat `unreal__create_entity` MCP tools.
Ducky keeps prefab helpers (`create_empty_prefab`, `create_prefab_from_entities`,
`instantiate_prefab`, `convert_actors_to_entities`) plus `scene_graph_capabilities`.
Epic toolsets speak **XYZ**; do not pass SpatialMath LUF into Epic `arguments`.
If `epic_mcp_online` is false, recite Epic setup steps — never pruned Ducky
`create_entity` / `list_entities`. Map: `skill_read_subskill("uefn", "epic_mcp")`.

**CRITICAL — editor mutations are SERIAL:** one heavy MCP call
(`unreal__*` / `instantiate_prefab` / `spawn_actor` / `wire_verse_device_ref` /
`save_current_level` / …) → wait → next. Never parallel or same-turn multi —
freezes UEFN. Details: `skill_read_subskill("uefn", "batch_commands")`. Button
devices for grants: nested Epic Creative devices (`creative_devices`).

Scene Graph is UEFN's entity-component system: **entities** are containers,
**components** add behavior/visuals (one component per class per entity), and
**prefabs** package entity trees into reusable assets. Editor-side structure is
built with the tools below; runtime behavior is written in Verse
(`/Verse.org/SceneGraph`).

The tools are **small composable primitives** — probe, read, create, change —
chain them for the task at hand.

**Prefab asset first.** Prefab-owned content is edited on the `.EntityPrefab`
asset (or packaged from *loose* level entities into a *new* prefab). Never treat
mutating a placed level instance as the primary workflow — see
`skill_read_subskill("scenegraph", "prefab_only")`.

## The tools (flat MCP tools)

| Kind | Tools |
|------|-------|
| **PROBE** | `scene_graph_capabilities` (prefab helpers); entity CRUD via Epic `ValkyrieToolset.EntityToolset` (`skill_read_subskill("uefn", "epic_mcp")`) |
| **PREFAB** | `create_empty_prefab`, `create_prefab_from_entities`, `instantiate_prefab`, `convert_actors_to_entities` |
| **VERSE API** | `get_verse_api`, `search_verse_digest`, `list_verse_modules` |

Always `scene_graph_capabilities({})` first for prefab helper availability. Entity
list/create uses Epic — not Ducky `list_entities` / `create_entity`.

## Golden path (build an entity in the editor)

```
scene_graph_capabilities({})
unreal__describe_toolset({ "toolset_name": "ValkyrieToolset.EntityToolset" })
unreal__call_tool({
  "toolset_name": "ValkyrieToolset.EntityToolset",
  "tool_name": "FindEntities",
  "arguments": {}
})
unreal__call_tool({
  "toolset_name": "ValkyrieToolset.EntityToolset",
  "tool_name": "CreateEntity",
  "arguments": { … }   # XYZ; follow describe_toolset schema / refPath
})
unreal__call_tool({
  "toolset_name": "ValkyrieToolset.EntityToolset",
  "tool_name": "AddComponent",
  "arguments": { … }
})
# Then SetComponentProperty / SetEntityTransform via the same toolset as needed.
# Prefab packaging stays on Ducky helpers below.
```

## Golden path (Entity Prefab — asset first, then place)

```
# Prefer blank asset + edit in UEFN prefab UI (Save the prefab):
create_empty_prefab({"prefab_name": "EP_Lamp", "folder": "/MyProject/Prefabs"})

# Or package LOOSE level entities into a NEW prefab (sources become an instance).
# NEVER call this on an already-placed EP_* instance — it can collapse the tree.
create_prefab_from_entities({
  "entity_names": ["Lamp"], "prefab_name": "EP_Lamp", "folder": "/MyProject/Prefabs"})

# Place always-on copies in the level (Content Browser drag equivalent):
instantiate_prefab({
  "prefab_path": "/MyProject/Prefabs/EP_Lamp",
  "translation": [800, 0, 0]})
save_current_level()
```

Static / always-on: prefab asset + `instantiate_prefab` + `save_current_level`.
Use Verse `P_*` spawn **only** for runtime spawn/despawn. For prefab-owned
structure/components after the asset exists: edit the `.EntityPrefab` in UEFN
and Save — MCP cannot see EntityPrefab editor tabs (transient worlds).

## Golden path (write Verse against Scene Graph)

```
get_verse_api({"name": "entity"})            # exact members on THIS build
get_verse_api({"name": "component"})         # lifecycle + TickEvents contract
get_verse_api({"name": "mesh_component"})    # before using any component API
get_verse_api({"name": "keyframed_movement_component"})  # BEFORE any motion
get_verse_api({"name": "inventory_component"})  # BEFORE granting items/weapons
get_verse_api({"name": "P_MyPrefab"})        # generated prefab class (Assets.digest)
# then write the .verse file with workspace_write_file and check workspace_list_verse_errors
```

Never guess a Verse signature — `get_verse_api` returns the real declaration
with doc comments from the project's digest files. `search_verse_digest` for
free-text hunts, `list_verse_modules` for the module map.

## Hard rules

- **Prefab asset first / never level-instance mutations as source of truth.**
  Prefab-owned hierarchy, meshes, and Verse comps belong on the `.EntityPrefab`
  (Save the prefab). Do not move bodies, add meshes, or attach comps on the
  placed level copy as the primary workflow — those become instance overrides
  (or destroy hierarchy). Details: `prefab_only`.
- **MCP cannot see EntityPrefab editor tabs** (transient worlds). Tools only
  list the open **level**. For prefab-owned edits: open the asset in UEFN UI
  and Save. Do not “fix it on the level instance instead.”
- **Never `create_prefab_from_entities` on an already-placed prefab instance** —
  packaging `EP_*` children into a new shell can collapse the tree. Only package
  *loose* level entities into a *new* prefab name.
- **ALWAYS digest-check before Scene Graph Verse** — `get_verse_api` /
  `search_verse_digest` for every unfamiliar type. Never invent APIs.
- **Motion over time = `keyframed_movement_component`**
  (`using { /Verse.org/SceneGraph/KeyframedMovement }`). Call
  `SetKeyframes([]keyframed_movement_delta, oneshot_/loop_/pingpong_…)` then
  `Play()` — `SetKeyframes` rebases onto the current transform and does **not**
  autoplay. Translation/Scale on deltas are **additive**. Prefer
  `linear_easing_function{}`. The class is `<final>`: compose, never subclass.
  Empty pivots need `transform_component` before KFM (`SetLocalTransform`
  creates one). **Never** use `creative_prop` / `animation_controller`
  keyframes for Scene Graph entities — different API.
- **Per-frame work = `TickEvents.PrePhysics` / `PostPhysics`**, subscribed in
  `OnBeginSimulation` and **cancelled in `OnEndSimulation`**. The callback
  payload is DeltaTime. `loop` + `Sleep(0.0)` is not a frame hook and is the
  usual reason generated motion stutters or never runs. `OnSimulate` runs
  **once** — wrap listeners in `loop`. Details: `verse_authoring`.
- **Follow/attach = origin, not per-tick copying.** `SetOrigin(entity_origin{
  Entity := Target})` / `ResetOrigin()` re-base an entity onto another without
  reparenting. Do not change origin and move in the same frame. Details:
  `movement_transforms`.
- **Components simulate in the editor as well as in play.** A static viewport
  usually means no `transform_component`, a component that was never attached
  (Verse not rebuilt), logic in the wrong hook, or a missing `Play()` — work
  the checklist in `movement_transforms`, then confirm in PIE / Launch Session.
- **No Scene Graph `button_component`.** Player interaction =
  `interactable_component` / `basic_interactable_component`. Creative
  `button_device` is a device, not an entity component. Catalog: `components`.
- **Weapons and items are entities, not devices.** Stock Fortnite guns are
  concrete classes under `/Fortnite.com/Weapons` / `/Fortnite.com/Items` —
  grant with `Inventory.AddItemDistribute(AssaultRifle_BR_CH4S1_Rare{})` after
  finding the agent's descendant `inventory_component`. Never `spawn_actor` a
  weapon class. Recipes: `itemization`. **Custom player firearms** are Entity
  Prefabs from `/Fortnite.com/Armory` templates (`assault_rifle_template`,
  pistol / shotgun / SMG) with `fort_trace_weapon_component` — mesh swap,
  tuning, and Verse grant/equip/clear/mutate: `custom_weapons`. Owned persist +
  `collectible_object_device` pickup + canvas shop + rejoin: verse
  `sys_owned_weapons`.
  **Custom non-weapon items** are blank Entity Prefabs with an itemization
  shell (`item_component` + pickup/description/icon/mesh) plus **your Verse
  components** for any equipped/dropped behavior (categories/stack/rarity,
  KFM, grant/equip) — no Creative granter path yet: `custom_items`.
  **Template abilities** (Spicy Sprint, status-effect AbilityElements,
  `fort_item_ability_component` + `fort_template_ability`) — `template_abilities`.
- **Mesh axis quirks**: put FBX yaw/pitch offsets on a **child** mesh entity
  (`SetLocalTransform`), keep root entity yaw = thrust/look heading.
- **SpatialMath axes, not Unreal axes**: translations/scales are
  `[forward, left, up]` (`left` = Unreal's -Y), rotations are quaternions
  `[x, y, z, w]`. All transform tools use this convention.
- **Property names are case-sensitive Verse digest names** (`Visible`,
  `Collidable`, `HideDuration`) — check `get_verse_api(<component>)` first. The
  mangled `__verse_0x...` storage names are handled internally; never pass them.
- **One component per subclass _group_ per entity** — not per class. All lights
  derive from `light_component`, so an entity holds **one light total**; two
  lights need two entities. Adding an existing class returns the one already
  there.
- **Asset components need PROJECT content**: mesh/particle/sound components
  reference the project's digest-generated asset classes; Fortnite `/Game/...`
  content will not attach. New island assets use `get_project_info().content_root`
  (never invent `/Game/...` for creates).
- **Entity names must be unique per level.** `create_entity` errors on
  duplicates; rename instead of recreating.
- **Entity Prefabs are first-class MCP tools.** `create_empty_prefab` /
  `create_prefab_from_entities` (loose entities → new name only) create assets
  under the project mount; `instantiate_prefab` places them via
  `spawn_actor_from_object` (same as Content Browser → `EntityProxyActor`). Do
  **not** `spawn_actor` an `EntityProxyActor` by class.
- **Module name collision** — do not put Verse under `Content/Verse/<Name>/`
  when `Content/<Name>/` already owns Assets module `Name`. Use a distinct
  folder (see `prefab_only` / `verse_authoring`).
- **Static vs dynamic:** always-on → prefab asset + `instantiate_prefab` +
  `save_current_level`. Runtime spawn/despawn → Verse `P_*{}` +
  `Sim.AddEntities` / `RemoveFromParent` after Verse rebuild (see
  `verse_authoring`).
- **Custom Verse components cannot be attached from the editor tools until the
  project's Verse has built** — write the `.verse` file, push changes, then the
  class exists to add in the editor (or add it in the Details panel). Project
  path spelling often: `/<Project>/_Verse.Verse-<Module>-<class_name>`.
- **Devices are not entities.** Existing device wiring stays on
  `wire_verse_device_ref` / `set_verse_editable`; Scene Graph tools only touch
  entities.

## After ANY scene graph change

`save_current_level()` for level/instance edits. Prefab-owned asset edits:
**Save the EntityPrefab** in UEFN. Nothing auto-saves.

## Reference files

Load with `skill_read_subskill("scenegraph", "<id>")`:

- `verse_authoring` — component lifecycle, per-frame `TickEvents`, runtime `P_*` spawn, hierarchy queries, module collision
- `editor_tools` — class resolution, asset comps, prefab packaging wrinkles, troubleshooting
- `components` — full builtin catalog, asset vs plain, `BasicShapes`, itemization comps, no `button_component`
- `prefab_only` — prefab-asset-first hard rules, MCP level-vs-tab limit, banned repackage, orbit recipe
- `movement_transforms` — why it isn't moving: local vs global, origins/attach, full KFM API, LUF axes, known transform bugs
- `itemization` — items and inventories, granting stock weapons from `/Fortnite.com/Weapons`, pickups, equipping
- `custom_weapons` — custom Armory Entity Prefabs (AR/pistol/shotgun/SMG), mesh/pivot/collision, `fort_trace_weapon_component`, Verse grant: WaitForInventory + AddItemDistribute then GetParentInventory/PickUp/Equip (not AddResult.Ok). Owned collectible + canvas shop + persist → verse `sys_owned_weapons`
- `custom_items` — fully custom non-weapon Entity Prefabs: itemization shell + Verse components for any behavior, categories/stack/rarity, KFM, equipped logic, Verse grant (no Creative granter yet)
- `template_abilities` — Fortnite template abilities: `fort_template_ability` Verse class, `fort_item_ability_component` on an item prefab, AbilityElements (burn/pepper), IA_Sprint, hotbar grant device
