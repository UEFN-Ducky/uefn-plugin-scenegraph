---
description: "Prefab-only hard rules — never mutate level instances; MCP cannot see EntityPrefab tabs; banned create_prefab_from_entities on instances; transform+KFM orbits; Verse module collisions"
metadata:
  order: 4
  label: "Prefab-only editing"
  default_enabled: false
  load_condition: "Editing EntityPrefabs, solar-system / orbit hierarchies, avoiding level-instance overrides, or packaging entities into prefabs"
---

## Prefab-only editing (hard rules)

**Edit the EntityPrefab asset — never the placed level instance as the source of truth.**

Mutating a level `EntityProxyActor` / prefab instance creates **instance overrides**
(or wrecks the tree). Do not move `Body_*`, attach meshes, or add Verse components
on the level copy as the primary workflow for prefab-owned content.

### MCP vs prefab asset tabs

- Prefab-editor windows are **transient worlds**. Scene Graph MCP tools only see
  the open **level**.
- For prefab-owned structure/components: open the `.EntityPrefab` in the UEFN
  Content Browser → edit the asset (Details → Add Component, hierarchy) → **Save
  the prefab**.
- Do **not** “fix it on the level instance instead” when the user asked for
  prefab-only edits. Tell the user to save the prefab asset.
- `open_asset_in_uefn` can reveal/open the prefab; tools still will not list that
  transient world’s entities.

### Banned / dangerous ops

| Never | Why |
|-------|-----|
| `create_prefab_from_entities` on an already-placed `EP_*` instance | Can collapse children into an empty shell (lost hierarchy). |
| Moving/editing `Body_*` / pivots only on the level instance | Instance overrides; other instances and the asset diverge. |
| Treating level `list_entities` results as the prefab asset | You are editing the instance, not the definition. |

### Allowed packaging

- `create_empty_prefab` — blank asset under the project mount; nothing placed.
- `create_prefab_from_entities` — only on **loose** level entities (not an existing
  prefab instance), into a **new** `prefab_name` (path must not already exist).
  Sources become an instance of the new prefab.
- `instantiate_prefab` — place always-on copies in the level (Content Browser drag
  equivalent). Call `save_current_level` after place.

### Place vs runtime spawn

| Goal | Path |
|------|------|
| Always-on / match-start | Prefab asset + `instantiate_prefab` + `save_current_level` |
| Runtime spawn/despawn | Verse `P_*{}` + `Sim.AddEntities` / `RemoveFromParent` after Verse rebuild |

---

## Orbit / motion recipe (prefab hierarchy)

Typical solar-system style tree (owned by the prefab):

```
EP_SolarSystem
  Sun                    (mesh)
  Pivot_Earth            (transform + constant_rotation / KFM)
    Body_Earth           (mesh + local Forward offset = orbit radius)
    Earth_Anchor
      Pivot_Luna         (transform + KFM)
        Body_Luna        (mesh + offset)
```

Rules:

1. **Pivots need `transform_component`.** Without it, `get_entity_info` shows
   `local_transform_error` and KFM cannot orbit children.
2. Put orbital radius on the **body** local translation; rotate the **pivot**.
3. Motion = `keyframed_movement_component`. The class is `<final>`, so a
   project `constant_rotation_component` **holds** one — it cannot extend it.
   Loop yaw with `loop_keyframed_movement_playback_mode`. Translation/Scale
   deltas additive (`0` = no change).
4. In Verse, before KFM: if no transform, call `SetLocalTransform` (creates
   `transform_component` on demand). Position the entity **before**
   `SetKeyframes` — it rebases onto the current transform — and remember
   `SetKeyframes` does not autoplay, so call `Play()`.
5. Attach custom Verse comps to the **prefab asset** after Verse build — or add
   in the prefab Details panel. Runtime AddComponents from a root component is
   OK if the root component lives on the prefab definition.
6. Components simulate in the editor as well as in play. If the orbit is still,
   walk the checklist in
   `skill_read_subskill("scenegraph", "movement_transforms")` and confirm in
   PIE / Launch Session.

---

## Verse module name collision

Do **not** put gameplay Verse under `Content/Verse/<Name>/` when
`Content/<Name>/` already owns Assets module `<Name>` (e.g. content folder
`SolarSystem` → Assets `SolarSystem` module). The Verse types may not resolve as
editor/project components.

Use a distinct folder/module (e.g. `Content/Verse/SolarOrbits/`).

Project component object path after compile often looks like:

`/<Project>/_Verse.Verse-<Module>-<class_name>`

---

## Checklist before claiming “prefab updated”

1. Changes are on the EntityPrefab asset (or explicitly applied to source), not
   only a level override.
2. Prefab saved in UEFN.
3. If Verse comps were added: Verse build succeeded; class visible to attach.
4. Pivots that move have `transform_component`, and KFM had `Play()` called.
5. User verified in **PIE / Launch Session** for runtime motion.
