---
source_plugin_id: scenegraph
name: scenegraph
description: "UEFN Scene Graph — create and edit entities, components, and prefabs in the editor via MCP tools, query the exact Verse API from digests, and author Verse components that compile first try"
license: All Rights Reserved
metadata:
  label: "UEFN Scene Graph"
  version: 3
  author: UEFN-Ducky
  copyright: Copyright 2026 UEFN-Ducky
  allow_redistribute: false
---

# UEFN Scene Graph — entities, components, prefabs

Scene Graph is UEFN's entity-component system: **entities** are containers,
**components** add behavior/visuals (one component per class per entity), and
**prefabs** package entity trees into reusable assets. Editor-side structure is
built with the tools below; runtime behavior is written in Verse
(`/Verse.org/SceneGraph`).

The tools are **small composable primitives** — probe, read, create, change —
chain them for the task at hand.

## The tools (flat MCP tools)

| Kind | Tools |
|------|-------|
| **PROBE** | `scene_graph_capabilities` |
| **READ** | `list_entities`, `get_entity_info`, `list_scene_component_classes`, `get_selected_entities`, `get_entity_component_property` |
| **CREATE** | `create_entity`, `add_entity_component`, `create_prefab_from_entities`, `instantiate_prefab` |
| **CHANGE** | `set_entity_transform`, `set_entity_component_property`, `rename_entity`, `set_entity_parent`, `duplicate_entity`, `select_entities` |
| **DESTROY** | `destroy_entity` (approval-gated), `remove_entity_component`, `convert_actors_to_entities` (approval-gated) |
| **VERSE API** | `get_verse_api`, `search_verse_digest`, `list_verse_modules` |

Always `scene_graph_capabilities({})` first — the scripting subsystem only
exists on newer UEFN builds. If it is missing the tools say so; do not retry.

## Golden path (build an entity in the editor)

```
scene_graph_capabilities({})                                   # PROBE
list_entities({})                                              # READ -> see what's there
create_entity({"name": "Lamp", "translation": [500, 0, 0]})    # CREATE
add_entity_component({"entity": "Lamp", "component_class": "mesh_component",
    "asset_path": "/MyProject/Meshes/SM_Lamp.SM_Lamp"})        # mesh needs a PROJECT asset
add_entity_component({"entity": "Lamp",
    "component_class": "spot_light_component"})                # plain component: no asset
set_entity_component_property({"entity": "Lamp",
    "component_class": "mesh_component",
    "prop": "Collidable", "value": true})                      # digest-name property
save_current_level()
```

## Golden path (write Verse against Scene Graph)

```
get_verse_api({"name": "entity"})            # exact members on THIS build
get_verse_api({"name": "mesh_component"})    # before using any component API
get_verse_api({"name": "keyframed_movement_component"})  # BEFORE any motion
get_verse_api({"name": "P_MyPrefab"})        # generated prefab class (Assets.digest)
# then write the .verse file with workspace_write_file and check workspace_list_verse_errors
```

Never guess a Verse signature — `get_verse_api` returns the real declaration
with doc comments from the project's digest files. `search_verse_digest` for
free-text hunts, `list_verse_modules` for the module map.

## Hard rules

- **ALWAYS digest-check before Scene Graph Verse** — `get_verse_api` /
  `search_verse_digest` for every unfamiliar type. Never invent APIs.
- **Motion over time = `keyframed_movement_component`**
  (`using { /Verse.org/SceneGraph/KeyframedMovement }`). Call
  `SetKeyframes([]keyframed_movement_delta, oneshot_/loop_/pingpong_…)` then
  `Play()`. Translation/Scale on deltas are **additive**. Prefer
  `linear_easing_function{}`. **Never** use `creative_prop` /
  `animation_controller` keyframes for Scene Graph entities — different API.
  **Never** spam per-tick `SetGlobalTransform` for flight/lerp (use KFM).
- **Mesh axis quirks**: put FBX yaw/pitch offsets on a **child** mesh entity
  (`SetLocalTransform`), keep root entity yaw = thrust/look heading.
- **SpatialMath axes, not Unreal axes**: translations/scales are
  `[forward, left, up]` (`left` = Unreal's -Y), rotations are quaternions
  `[x, y, z, w]`. All transform tools use this convention.
- **Property names are case-sensitive Verse digest names** (`Visible`,
  `Collidable`, `HideDuration`) — check `get_verse_api(<component>)` first. The
  mangled `__verse_0x...` storage names are handled internally; never pass them.
- **One component of a given class per entity** — adding an existing class
  returns the one already there.
- **Asset components need PROJECT content**: mesh/particle/sound components
  reference the project's digest-generated asset classes; Fortnite `/Game/...`
  content will not attach. New island assets use `get_project_info().content_root`
  (never invent `/Game/...` for creates).
- **Entity names must be unique per level.** `create_entity` errors on
  duplicates; rename instead of recreating.
- **Prefab scripting is WIP in UEFN.** `create_prefab_from_entities` works (the
  sources become an instance); `instantiate_prefab` is best-effort — when it
  refuses, place instances from the Content Browser or spawn them in Verse.
- **Custom Verse components cannot be attached from the editor tools until the
  project's Verse has built** — write the `.verse` file, push changes, then the
  class exists to add in the editor (or add it in the Details panel).
- **Devices are not entities.** Existing device wiring stays on
  `wire_verse_device_ref` / `set_verse_editable`; Scene Graph tools only touch
  entities.

## After ANY scene graph change

`save_current_level()` — entities live in the level. Nothing auto-saves.
