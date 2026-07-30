---
description: "Deep Verse authoring for Scene Graph: custom component lifecycle, spawning prefabs at runtime, hierarchy queries, events, tags, and SpatialMath transforms — with build-verified signatures"
metadata:
  order: 1
  label: "Verse authoring (components & prefabs)"
  default_enabled: false
  load_condition: "Writing or debugging Verse that defines a component, spawns/queries entities or prefabs, or manipulates entity transforms"
---

## Verse authoring for Scene Graph

Imports for almost everything here:

```verse
using { /Verse.org/SceneGraph }
using { /Verse.org/Simulation }
using { /Verse.org/SpatialMath }
```

Confirm any signature with `get_verse_api({"name": "<identifier>"})` before
using it — it returns the declaration from THIS build's digests.

### Custom component

```verse
door_opener_component := class<final_super>(component):
    @editable
    OpenSpeed:float = 1.0

    OnBeginSimulation<override>():void =
        (super:)OnBeginSimulation()
        # synchronous setup: cache references, subscribe to events

    OnSimulate<override>()<suspends>:void =
        # async behavior; this task is cancelled before OnEndSimulation
        loop:
            Sleep(1.0)
```

Lifecycle order (from the `component` digest):

1. `OnAddedToScene` — entity entered the scene; component queries are valid after this.
2. `OnBeginSimulation` — set up TickEvents callbacks / guaranteed-immediate setup.
3. `OnSimulate` (`<suspends>`) — long-running behavior; cancelled before step 4.
4. `OnEndSimulation` — cancel cached cancelables (experience reset or entity removed).
5. `OnRemovingFromScene` — final cleanup before disposal.

Also on `component`: `Entity` (the owner), `RemoveFromEntity()`,
`IsInScene[]`, `IsSimulating[]`, `SendDown(event)`, `OnReceive(event)`
(override, return `true` to consume), and `TickEvents` (PrePhysics/PostPhysics
per-frame callbacks).

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

Prefabs created in the editor generate a Verse class (and an `entity_prefab`
asset ref) in **Assets.digest.verse** on the next Verse build:

```verse
# Assets.digest.verse (generated — never edit):
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

`vector3` fields are `Forward` (was X), `Left` (was -Y), `Up` (was Z).
`transform` is `{Translation:vector3, Rotation:rotation, Scale:vector3}`.

- Entity extensions: `GetGlobalTransform()`, `GetLocalTransform()`,
  `SetGlobalTransform(t)`, `SetLocalTransform(t)` (create a
  `transform_component` on demand), plus `SetOrigin`/`ResetOrigin`.
- Rotations: `MakeRotationFromYawPitchRollDegrees(Yaw, Pitch, Roll)`,
  `MakeRotationDegrees(Axis, Angle)`, `Slerp`, `.GetForwardAxis()`,
  `.Invert()`; combine with `*`.
- Movement over time: prefer `keyframed_movement_component`
  (`SceneGraph.KeyframedMovement` module) over per-tick `SetGlobalTransform` —
  it interpolates client-side.

### Keyframed movement (the motion API — digest-check always)

```verse
using { /Verse.org/SceneGraph/KeyframedMovement }

# NEVER creative_prop animation_controller for Scene Graph entities.
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

### Built-in components worth knowing

`mesh_component` (Visible/Collidable/Queryable vars,
EntityEnteredEvent/EntityExitedEvent), `particle_system_component`,
`sound_component`, `light_component` family (spot/sphere/rect/capsule/
directional), `camera_component` family + `camera_director_component`,
`interactable_component` / `basic_interactable_component`,
`possessable_component`, `rarity_component`, `stackable_component`,
`transform_component`, `keyframed_movement_component`. Collision queries:
`FindOverlapHits` / `FindSweepHits` with `collision_sphere/box/capsule/point`.

### Performance rules (Epic's guidance)

- Find children once at simulation start; store references or subscribe to
  events instead of re-querying wide hierarchies during gameplay.
- Keep interactions inside the prefab's local hierarchy; avoid broadcasting
  `SendDown` from the simulation root.
- Put logic in components, not in `entity` subclasses — restructure-friendly.
