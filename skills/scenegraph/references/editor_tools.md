---
description: "Deep editor-tool workflow for Scene Graph: component class resolution, asset components, prefab creation wrinkles, actor conversion, and troubleshooting capability misses"
metadata:
  order: 2
  label: "Editor tools (deep workflow)"
  default_enabled: false
  load_condition: "A scene graph tool errored or refused, a component class will not resolve, prefab creation/instantiation is involved, or actors need converting to entities"
---

## Scene Graph editor tools — beyond the golden path

### Reading `scene_graph_capabilities`

```
{"script_subsystem": true, "converter_subsystem": true,
 "builtin_component_classes": {"mesh_component": true, ...},
 "entities_in_level": 5}
```

- `script_subsystem: false` → this UEFN build has no Scene Graph scripting;
  nothing else in this pack's editor tools will work. Say so — do not fall back
  to `execute_python` guessing.
- A `false` builtin class → that alias is missing on this build; use
  `list_scene_component_classes` to see what exists.

### Component class resolution in `add_entity_component`

Three spellings, tried in order:

1. **Alias** — `mesh_component`, `spot_light_component`,
   `keyframed_movement_component`, ... (see capabilities probe for the list).
2. **Verse class name** — any name from `list_scene_component_classes`,
   including the project's own Verse components (kind `project`) once the
   project's Verse has built.
3. **Full class object path** — e.g.
   `/MyProject/_Verse/Assets.Props-SM_Rock` (kind `asset_generated`).

`list_scene_component_classes({"search": "light"})` filters by substring; kinds
are `builtin` (engine), `project` (your Verse code), `asset_generated`
(digest classes for meshes/particles/sounds in project content).

### Asset components

`add_entity_component` with `asset_path` wires a mesh/particle/sound asset:

- The asset MUST live in the project mount (`/MyProject/...`). `/Game/...`
  Fortnite content has no digest class — the tool errors, that is by design.
- The resulting component's class is the asset's generated class (e.g.
  `Props-SM_Rock`), a subclass of `mesh_component` — reading/removing it by
  `mesh_component` still works (base-class match).
- Import new content first with the asset pipeline tools, then attach it.

### Entities vs the outliner

- Entities live under the level's `LevelEntity` container; the simulation root
  (`SimulationEntity`) and `LevelEntity` show up in `list_entities` as
  infrastructure — do not destroy or reparent them.
- `destroy_entity` soft-deletes (the object becomes `TRASH_*` until save); the
  tools filter trash out of listings automatically.
- Prefab-editor windows run in transient worlds; the tools only report the
  open level's world.

### Prefabs (prefab asset first)

Hard rules and orbit pitfalls: `skill_read_subskill("scenegraph", "prefab_only")`.

- `create_empty_prefab` creates a blank `EntityPrefab` asset under the project
  mount (e.g. `/MyProject/SolarSystem/EP_Thing`) and saves it. Nothing is
  placed in the level. Prefer this + edit/Save in the UEFN prefab UI for
  prefab-owned structure.
- `create_prefab_from_entities` packages **loose** named entities and REPLACES
  them in the level with an instance of the **new** prefab. The asset saves
  immediately; its Verse class appears in Assets.digest.verse only after the
  next Verse build. Fails if the asset path already exists — pick a new
  `prefab_name`.
- **NEVER** `create_prefab_from_entities` on an already-placed `EP_*` instance
  (or its children) to “save overrides back” — that can collapse the hierarchy
  into an empty shell. Destroy broken instances, re-`instantiate_prefab` the
  original asset, and edit the prefab in UEFN UI instead.
- `instantiate_prefab` places via `EditorActorSubsystem.spawn_actor_from_object`
  on the EntityPrefab (same as Content Browser drag). Result: an
  `EntityProxyActor` wrapping the prefab entity under `LevelEntity`. Optional
  SpatialMath `translation` `[forward, left, up]`. Do not spawn
  `EntityProxyActor` by class with `spawn_actor`.
- Prefab-editor windows run in transient worlds; the tools only report the
  open level's world. For prefab-owned content: open the `.EntityPrefab` in
  UEFN and Save. Do not treat level-instance edits as the source of truth.
- Prefab overrides (per-instance property tweaks) are NOT a separate scripting
  API — prefer editing the prefab asset; level tweaks diverge other instances.
- `list_entities` filters `TRASH_*`, `REINST_*`, and EntityProxyActor shadow
  copies so each placed prefab appears once (canonical LevelEntity path).

### Static vs Verse spawn

- Always-on / match-start: prefab asset + `instantiate_prefab` +
  `save_current_level`.
- Runtime spawn/despawn: Verse `P_*{}` + `Sim.AddEntities` (see
  `verse_authoring`) after Verse rebuild.

### Converting actors

`convert_actors_to_entities` (approval-gated) runs Epic's converter subsystem
on specific actors. It is one-way — confirm with the user, and
`save_current_level` after. Not every actor class is convertible; the tool
reports per-actor results. Devices should stay devices.

### Troubleshooting

- **"No editable property 'X'"** — property names are case-sensitive digest
  names; run `get_verse_api({"name": "<component class>"})` and use the `var`
  field name exactly (`Visible`, not `visible`).
- **Ambiguous entity name** — multiple matches are listed in the error; pass
  the full object path instead of the display name.
- **Transform moved the wrong way** — remember `[forward, left, up]`:
  `left: 50` is Unreal `Y = -50`. Verify with `get_entity_info` bounds.
- **Component missing after project Verse edit** — the editor needs a Verse
  build before new project component classes exist; push changes and retry.
  Project paths often look like
  `/<Project>/_Verse.Verse-<Module>-<class_name>`.
- **Changes gone after UEFN restart** — `save_current_level()` was skipped
  (level) or the EntityPrefab was not Saved (asset).
- **Prefab hierarchy vanished after packaging** — you likely ran
  `create_prefab_from_entities` on an existing instance; restore via
  `instantiate_prefab` of the original asset (see `prefab_only`).
- **Pivot won't orbit / `local_transform_error`** — add `transform_component`
  (or `SetLocalTransform` in Verse) before KFM.
