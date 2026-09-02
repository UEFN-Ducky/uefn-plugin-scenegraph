---
description: "Why Scene Graph entities do not move — transform_component local vs global, origins for attaching to players, full keyframed_movement_component API, TickEvents vs KFM, LUF axes, deep-hierarchy transform bug"
metadata:
  order: 5
  label: "Movement & transforms (why it isn't moving)"
  default_enabled: false
  load_condition: "An entity will not move, rotate, animate or follow something; attaching entities to players/vehicles; orbits and movers; keyframed movement; transforms applying to the wrong axis or not at all"
---

## Movement & transforms

Every signature here is from this build's digests. Re-check with
`get_verse_api({"name": "<identifier>"})` before writing anything unfamiliar.

```verse
using { /Verse.org/SceneGraph }
using { /Verse.org/SceneGraph/KeyframedMovement }
using { /Verse.org/SpatialMath }
using { /Fortnite.com/Characters }   # fort_character / GetFortCharacter[] in the origin recipe below
```

### Pick the right mechanism

| Goal | Use | Not |
|------|-----|-----|
| Teleport / place once | `SetLocalTransform` / `SetGlobalTransform` | a tick loop |
| Timed or looping animation (doors, lifts, orbits, projectile flight) | `keyframed_movement_component` | per-frame transform writes |
| Per-frame steering, chasing, physics-reactive motion | `TickEvents.PrePhysics` (see `verse_authoring`) | `loop` + `Sleep(0.0)` |
| Follow / attach to a player, vehicle or other entity | **origin** (`SetOrigin`) | copying the target transform every frame |
| Reparent permanently | `Parent.AddEntities(array{Child})` | `SetOrigin` |

### `transform_component`

`class<final><final_super>(component)` — one per entity, and **required for a
mesh to be positioned at all** (`mesh_component`'s digest lists it as a
dependency).

| Member | Meaning |
|--------|---------|
| `var GlobalTransform:transform` | World-space pose. A value set at construction is **overwritten** by the local calculation. |
| `var LocalTransform:transform` | Pose relative to the parent, or to `Origin` when one is set. |
| `var Origin:?origin` | Alternative origin instead of the parent entity. |

Entity extensions (`/Verse.org/SceneGraph`):

```verse
(InEntity:entity).GetGlobalTransform()<transacts>:transform
(InEntity:entity).GetLocalTransform()<transacts>:transform
(InEntity:entity).SetGlobalTransform(NewGlobalTransform:transform)<transacts>:void
(InEntity:entity).SetLocalTransform(NewLocalTransform:transform)<transacts>:void
(InEntity:entity).SetOrigin(NewOrigin:origin)<transacts>:void
(InEntity:entity).ResetOrigin()<transacts>:void
```

`SetLocalTransform` **creates a `transform_component` on demand**, which is the
one-liner fix for an empty pivot that reports `local_transform_error`:

```verse
Ent.SetLocalTransform(Ent.GetLocalTransform())   # ensure a transform exists
```

### Attaching with an origin

An origin re-bases an entity's local transform onto another entity without
reparenting it — this is how you make something follow a player, a vehicle, or
a moving platform.

```verse
if:
    Character := Agent.GetFortCharacter[]
    CharacterEntity := Character.GetEntity[]
then:
    Held.SetOrigin(entity_origin{Entity := CharacterEntity})
    Held.SetLocalTransform(transform{Translation := vector3{Up := 90.0}})

# later
Held.ResetOrigin()
```

`origin` is an interface with `GetTransform()`; `entity_origin` is the
entity-backed implementation (`Entity` field).

**Do not change the origin and move in the same frame** — that combination
stopped working in 40.00 (Epic bug report still open). Set the origin, let a
frame pass (`Sleep(0.0)` in a `<suspends>` context, or act on the next tick),
then set the transform. The same "too fast" class of bug leaves the mesh behind
while collision moves, so avoid rapid attach/detach/move bursts.

### `keyframed_movement_component`

`class<final><final_super>(component)` — **`<final>`, so it cannot be
subclassed.** A `constant_rotation_component` of your own *holds* a KFM; it
never extends one. Playback happens in the **Pre-Physics** tick phase.

| Member | Notes |
|--------|-------|
| `SetKeyframes(RelativeKeyframes:[]keyframed_movement_delta, PlaybackMode:keyframed_movement_playback_mode)` | Stops any current animation, **rebases the path onto the entity's current transform**, and does **not** start playing. |
| `Play()` / `Pause()` | Pause keeps the position; Play resumes from there. |
| `Stop()` / `Stop(BlendOutTime:float)` | Resets to the initial transform; the next `Play()` starts over. |
| `IsPlaying[]` / `IsPaused[]` / `HasValidAnimation[]` | Failable state checks. |
| `var Duration:?float` | Fails when there is no fixed duration (looping). |
| `PlayedEvent` / `PausedEvent` / `StoppedEvent` / `FinishedEvent` | `listenable(tuple())`. `FinishedEvent` never fires for infinite animations. |
| `KeyframeReachedEvent` | `listenable(tuple(int, logic))` — keyframe index and whether playback is reversed. |

```verse
KFM := keyframed_movement_component{Entity := Ent}
Ent.AddComponents(array{KFM})

KF := keyframed_movement_delta:
    Transform := transform:
        Translation := vector3{Forward := 500.0}   # ADDITIVE delta, not a destination
        Rotation := IdentityRotation()
        Scale := vector3{}                         # 0 = no change (additive)
    Duration := 2.0
    Easing := linear_easing_function{}

Ent.SetGlobalTransform(StartPose)       # position BEFORE SetKeyframes (it rebases)
KFM.SetKeyframes(array{KF}, oneshot_keyframed_movement_playback_mode{})
KFM.Play()                              # nothing moves without this
```

Playback modes: `oneshot_`, `loop_`, `pingpong_keyframed_movement_playback_mode`.
Translation and Scale on a delta are **additive**; Rotation is relative.
Never drive Scene Graph entities with `creative_prop` / `animation_controller`
keyframes — different system, different API.

### Axes and coordinate systems

`vector3` is `Forward` (old X), `Left` (old -Y), `Up` (old Z); `transform` is
`{Translation, Rotation, Scale}`; rotations are quaternions built with
`MakeRotationFromYawPitchRollDegrees` / `MakeRotationDegrees`, combined with `*`.

`/Verse.org/SpatialMath` is the LUF system used by Scene Graph and the editor.
There is a second, legacy XYZ-convention copy of these types in
`/UnrealEngine.com/Temporary/SpatialMath` — `rotation`, `transform` and even
`IdentityRotation()` exist in both. In a file that imports both families,
**qualify the type** the way the digests do —
`(/Verse.org/SpatialMath:)transform` — or transforms come out silently rotated
or offset. Imported FBX assets should be configured so
their Up/Forward match LUF; otherwise put the axis correction on a **child**
mesh entity via `SetLocalTransform` and keep the root's yaw as the real heading.

### When nothing moves — checklist

Components are documented to simulate in the **editor as well as in play**, so a
dead viewport is usually a real bug, not "you forgot to hit Play". Work down
this list, then confirm in PIE / Launch Session before declaring it broken:

1. Is there a `transform_component`? EntityToolset `FindEntities` reporting
   `local_transform_error` means no. Call `SetLocalTransform` or add one.
2. Is the component actually attached? Custom Verse components only appear
   after a successful Verse build — check the EntityToolset component listing (`unreal__describe_toolset` for the exact tool name).
3. Is the work in the right hook? Setup in `OnBeginSimulation`, async in
   `OnSimulate` (runs **once** — wrap listeners in `loop`), per-frame in
   `TickEvents.PrePhysics`.
4. KFM: did you call `Play()` after `SetKeyframes`? Are the deltas non-zero
   (they are additive, `0` means no change)?
5. Are you moving the right entity? Orbit radius belongs on the **body**'s local
   translation; the **pivot** is what rotates.
6. Did a `<decides>` call fail silently inside an `if`? `GetFortCharacter[]`,
   `GetEntity[]`, `GetSimulationEntity[]` and `GetComponent[]` all fail rather
   than error.

### Known transform bugs worth designing around

- **`GetGlobalTransform` on deep children.** Three or more levels down it can
  return `0,0,0` (it appears to return the local transform). Epic tracks this as
  FORT-1026495, status Backlogged. Prefer `GetLocalTransform` /
  `SetLocalTransform` for children, and parent a spawned entity **directly to
  its intended parent** rather than adding it to `SimulationEntity` first.
- **`-0.0` transform values.** Prefabs or placed objects carrying `-0` instead
  of `0` broke island launch in 39.20. Write `0.0`.
- **Same-frame origin change plus move** — see the attach section above.
