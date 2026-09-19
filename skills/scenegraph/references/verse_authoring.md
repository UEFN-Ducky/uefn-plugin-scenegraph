---
description: "Deep Verse authoring for Scene Graph: custom component lifecycle, per-frame TickEvents, spawning prefabs at runtime, hierarchy queries, events, tags, and SpatialMath transforms — with build-verified signatures"
metadata:
  order: 1
  label: "Verse authoring (components & prefabs)"
  default_enabled: false
  load_condition: "Writing or debugging Verse that defines a component, needs a per-frame update, spawns/queries entities or prefabs, or manipulates entity transforms"
---

## Verse authoring for Scene Graph

> **Snippets here are fragments.** The `using` block in this file's first code
> block applies to all of them — copy those imports (or start from the matching
> `verse_template_apply` pack) when pasting into a real `.verse` file.

Imports for almost everything here:

```verse
using { /Verse.org/SceneGraph }
using { /Verse.org/Simulation }
using { /Verse.org/SpatialMath }
```

Confirm any signature with `get_verse_api({"name": "<identifier>"})` before
using it — it returns the declaration from THIS build's digests.

### Custom component

`<final_super>` is **required** — without it the class cannot be added to an
entity. Subclasses of your component do not repeat it.

```verse
door_opener_component := class<final_super>(component):
    @editable
    OpenSpeed:float = 1.0

    OnBeginSimulation<override>():void =
        (super:)OnBeginSimulation()
        # synchronous setup: cache references, subscribe to events

    OnSimulate<override>()<suspends>:void =
        # async behavior; runs ONCE, so wrap listeners in loop.
        # This task is cancelled before OnEndSimulation.
        loop:
            Sleep(1.0)
```

Lifecycle order (from the `component` digest doc block):

1. `OnAddedToScene` — entity entered the scene; component queries are valid
   *after* this completes.
2. `OnBeginSimulation` — guaranteed-immediate setup: cache lookups, subscribe
   `TickEvents`. Runs after `OnAddedToScene`, before `OnSimulate`.
3. `OnSimulate` (`<suspends>`) — long-running async behavior. Called once;
   cancelled before step 4.
4. `OnEndSimulation` — experience reset or entity removed from the scene.
   Cancel every cancelable you cached. Only runs if `OnBeginSimulation` ran.
5. `OnRemovingFromScene` — final cleanup before disposal.

Rules the digest states outright:

- **One component per subclass _group_**, not per class. All the lights derive
  from `light_component`, so an entity can hold **one** light total — a spot and
  a sphere light need two entities.
- `GetComponent` / `AddComponents` **phase-sync**: called during the
  AddedToScene or BeginSimulation phase, they guarantee the returned or added
  component has reached that same phase. That is why caching in
  `OnBeginSimulation` is safe and querying earlier is not.
- **Keep logic in components, not in `entity` subclasses.** Epic's own note on
  `entity`: prefabs get restructured constantly during production, and code on
  the entity class forces refactors.
- Components simulate in the **editor as well as in play**. If nothing happens
  in the viewport see the checklist in `movement_transforms`, then confirm in
  PIE before calling it broken.

Also on `component`: `Entity` (the owner), `RemoveFromEntity()`,
`IsInScene[]`, `IsSimulating[]`, `SendDown(event)`, `OnReceive(event)`
(override, return `true` to consume — `MinUploadedAtFNVersion := 4000`), and
`TickEvents`.

### Per-frame work: `OnSimulate` loop (TickEvents is Epic-only on 42.10)

**`TickEvents.PrePhysics.Subscribe(...)` does NOT compile in creator code.**
`execution_listenable` is declared `class<epic_internal>` in the 42.10 digest, so
subscribing from your own component fails the build:

```
Invalid access of internal function (/Verse.org/SceneGraph/execution_listenable:)Subscribe
from control scope .../mover_component/OnBeginSimulation
```

(Verified by compiling on FN 42.10. Re-check with
`get_verse_api("execution_listenable")` — if Epic drops `epic_internal`, the
subscribe form below becomes usable again.)

The per-frame hook creator code *can* use is `OnSimulate` with a one-frame
`Sleep(0.0)` and your own delta clock:

```verse
using { /Verse.org/SpatialMath }
mover_component := class<final_super>(component):
    @editable Speed:float = 200.0

    OnSimulate<override>()<suspends>:void =
        var Last:float = GetSimulationElapsedTime()
        loop:
            Sleep(0.0)                      # yields exactly one frame
            if (not IsSimulating[]):
                break                       # entity left the scene / experience reset
            Now := GetSimulationElapsedTime()
            Advance(Now - Last)
            set Last = Now

    Advance(DeltaTime:float):void =
        T := Entity.GetLocalTransform()
        Entity.SetLocalTransform(transform:
            Translation := T.Translation + vector3{Forward := Speed * DeltaTime}
            Rotation := T.Rotation
            Scale := T.Scale)
```

- Use a **measured** delta (`GetSimulationElapsedTime` difference), never a fixed
  constant — `Sleep(0.0)` resumes next frame, not on a fixed cadence.
- `OnSimulate` is cancelled before `OnEndSimulation`, so this loop needs no manual
  cancel; the `IsSimulating[]` break is belt-and-braces for editor resets.
- For timed, repeatable motion (doors, lifts, orbits) prefer
  `keyframed_movement_component` over any hand-rolled loop — see
  `movement_transforms`.
- `TickEvents` still exists on `component` and PrePhysics/PostPhysics remain the
  right *concepts* (affect this frame's physics vs react to its result); only the
  `Subscribe` call is gated.
- Scale motion by `DeltaTime`; never assume a fixed frame rate.
- For timed or looping animation prefer `keyframed_movement_component` over
  ticking a transform yourself — see `movement_transforms`.

### Entity API (verified members)

- Hierarchy: `GetParent[]`, `GetEntities()`, `AddEntities(array{...})`,
  `RemoveFromParent()`.
- Components: `GetComponent[type]` (failable), `GetComponents()`,
  `AddComponents(array{...})`.
- Events: `SendUp(event)` / `SendDown(event)` — propagation stops when consumed.
- Tags: `AddTag`, `RemoveTag`, `ContainsTag[]`, `ContainsAllTags[]`, `ContainsAnyTag[]`.
- Queries (extension functions, return generators):
  `FindDescendantEntities(type)`, `FindDescendantEntitiesWithComponent(type)`,
  `FindDescendantComponents(type)`, plus `FindAncestor*` mirrors and
  `Find{Descendant,Ancestor}EntitiesWithTag(tag_type)`.
- Cache lookups at `OnBeginSimulation` and react to events — do not rescan the
  hierarchy every tick.

### Spawning a prefab at runtime

Use this **only for dynamic** spawn/despawn (waves, interact, inventory).
Always-on scenery should be placed once with `instantiate_prefab` +
`save_current_level` — not spawned from Verse every match.

Prefabs created in the editor generate a Verse class (and an `entity_prefab`
asset ref) in **Assets.digest.verse** on the next Verse build:

```verse
# Assets.digest.verse (generated — NEVER edit / write / delete):
#   P_LightPost := class<final>(entity):
#   P_LightPost_asset : entity_prefab = external {}
```

Spawn an instance by instantiating the class and parenting it into the scene:

```verse
if (Sim := Entity.GetSimulationEntity[]):
    LightPost := P_LightPost{}
    Sim.AddEntities(array{LightPost})
    LightPost.SetGlobalTransform(transform{Translation := vector3{Forward := 500.0, Left := 0.0, Up := 0.0}})
```

Despawn with `LightPost.RemoveFromParent()`. Re-add later with `AddEntities`.
If the prefab class is not found, the project has not rebuilt Verse since the
prefab was created — build/push Verse changes first, then check
`get_verse_api({"name": "P_<name>"})`.

### Transforms (SpatialMath)

Full treatment — local vs global, origins, attaching to a player, the
deep-hierarchy bug: `skill_read_subskill("scenegraph", "movement_transforms")`.

`vector3` fields are `Forward` (was X), `Left` (was -Y), `Up` (was Z).
`transform` is `{Translation:vector3, Rotation:rotation, Scale:vector3}`.

`/Verse.org/SpatialMath` is the LUF system. `/UnrealEngine.com` and
`/Fortnite.com` carry their own legacy XYZ transform/vector types, so in a file
importing both families **qualify the type** exactly like the digests do:
`(/Verse.org/SpatialMath:)transform`. Mixing them silently misaligns motion.

- Entity extensions: `GetGlobalTransform()`, `GetLocalTransform()`,
  `SetGlobalTransform(t)`, `SetLocalTransform(t)` (create a
  `transform_component` on demand), plus `SetOrigin`/`ResetOrigin`.
- Rotations: `MakeRotationFromYawPitchRollDegrees(Yaw, Pitch, Roll)`,
  `MakeRotationDegrees(Axis, Angle)`, `Slerp`, `.GetForwardAxis()`,
  `.Invert()`; combine with `*`.
- Movement over time: prefer `keyframed_movement_component`
  (`SceneGraph.KeyframedMovement` module) over per-tick `SetGlobalTransform` —
  it interpolates client-side.

### Ensure transform before KFM

Empty pivots often have **no** `transform_component` (`local_transform_error`
from EntityToolset `FindEntities`). KFM cannot drive them until a transform exists.

```verse
# SetLocalTransform creates transform_component on demand if missing.
Ent.SetLocalTransform(Ent.GetLocalTransform())
```

Do this (or add `transform_component` in the prefab) **before** attaching /
playing `keyframed_movement_component`. Orbits and looping yaw run in **PIE**,
not the idle editor viewport.

### Keyframed movement (the motion API — digest-check always)

`keyframed_movement_component` is `class<final><final_super>(component)`: you
**cannot subclass it**. A custom `constant_rotation_component` *holds* a KFM, it
does not extend one. `SetKeyframes` rebases the path relative to the entity's
**current** transform and does not start playback — position first, then
`SetKeyframes`, then `Play()`. Full API in `movement_transforms`.

```verse
using { /Verse.org/SceneGraph/KeyframedMovement }

# NEVER creative_prop animation_controller for Scene Graph entities.
# Ensure transform exists first (see above).
KFM := keyframed_movement_component{Entity := Ent}
Ent.AddComponents(array{KFM})
KF := keyframed_movement_delta:
    Transform := transform{
        Translation := DeltaLoc          # additive
        Rotation := DeltaRot             # relative
        Scale := vector3{Forward := 0.0, Left := 0.0, Up := 0.0}  # additive; 0 = no change
    }
    Duration := 0.2
    Easing := linear_easing_function{}
KFM.SetKeyframes(array{KF}, oneshot_keyframed_movement_playback_mode{})
KFM.Play()
```

Playback modes: `oneshot_keyframed_movement_playback_mode`,
`loop_keyframed_movement_playback_mode`, `pingpong_keyframed_movement_playback_mode`.
Confirm with `get_verse_api({"name": "keyframed_movement_component"})`.

Mesh nose wrong (FBX axis): child entity + `SetLocalTransform` yaw offset;
keep root heading = thrust/look.

### Module name collision

Do **not** put gameplay Verse under `Content/Verse/<Name>/` when
`Content/<Name>/` already owns Assets module `<Name>` (e.g. content folder
`SolarSystem`). Types may not resolve as editor/project components. Use a
distinct folder/module (e.g. `Verse/SolarOrbits/`).

After Verse build, project component object paths often look like:

`/<Project>/_Verse.Verse-<Module>-<class_name>`

Use that full path with EntityToolset `AddComponent` when the short alias fails.
Attach custom comps on the **prefab asset** when possible (see `prefab_only`).

### Built-in components worth knowing

Full catalog: `skill_read_subskill("scenegraph", "components")`. Items,
inventories and weapon granting: `skill_read_subskill("scenegraph", "itemization")`.

Prototyping meshes with **no project asset**: `/UnrealEngine.com/BasicShapes`
gives `cube`, `sphere`, `plane`, `cone`, `cylinder`, each a `mesh_component`
subclass — `Shape := sphere{Entity := Ent}` then `Ent.AddComponents(array{Shape})`.

`mesh_component` (Visible/Collidable/Queryable vars,
EntityEnteredEvent/EntityExitedEvent), `particle_system_component`,
`sound_component`, `light_component` family (spot/sphere/rect/capsule/
directional), `camera_component` family + `camera_director_component`,
`interactable_component` / `basic_interactable_component` (there is **no**
Scene Graph `button_component`), `possessable_component`, `rarity_component`,
`stackable_component` / `basic_stackable_component`, `transform_component`,
`keyframed_movement_component`, `mass_component`, `icon_component`. Collision
queries: `FindOverlapHits` / `FindSweepHits` with
`collision_sphere/box/capsule/point`.

### Performance rules (Epic's guidance)

- Find children once at simulation start; store references or subscribe to
  events instead of re-querying wide hierarchies during gameplay.
- Keep interactions inside the prefab's local hierarchy; avoid broadcasting
  `SendDown` from the simulation root.
- One `TickEvents` subscription doing a little work beats several components
  each ticking; cancel them all in `OnEndSimulation`.
