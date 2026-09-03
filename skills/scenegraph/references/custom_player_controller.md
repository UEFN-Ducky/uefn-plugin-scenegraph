---
description: "Fully custom player controller on a Scene Graph entity — 42.10 Move/Jump input actions, a Verse movement component with editable speed/accel/friction/gravity/jump, orbit camera via fort_orbit_camera_modifier, stock fort_character parked in stasis; compiled templates and the exact gotchas"
metadata:
  order: 12
  label: "Custom entity player controller"
  default_enabled: false
  load_condition: "User wants fully custom player movement/locomotion instead of Fortnite character movement, a custom player entity/pawn, custom jump force or gravity or speed, the new Move input action, or a scene graph orbit camera following their own entity"
---

## Custom entity player controller

> **Snippets here are fragments.** The `using` block below applies to all of them.

Replace Fortnite character movement with your own: the player drives a **Scene
Graph entity** you integrate yourself, an **orbit camera modifier** follows it,
and the stock `fort_character` is parked so it cannot fight your motion. Every
number (speed, acceleration, friction, gravity, jump impulse) is an `@editable`.

> **Experimental — cannot be published.** The `Move` / `Interact` input actions
> (`/Fortnite.com/Input/Character`), the Scene Graph camera components and the
> `fort_*` camera modifiers all emit `Script warning 2304`. Tell the user this
> first. Everything below compiles in UEFN with **0 errors**.

### Start from the compiled templates

```
verse_template_apply("custom_movement")     # both files -> Verse/CustomMovement/
```

- `player_movement_component.verse` — the per-entity integrator (component).
- `custom_movement_controller.verse` — the `creative_device` that binds input,
  claims the camera, and parks the stock character.

Don't retype these from memory; apply the pack, then tune.

### Rig layout (build in the editor first)

```
RigRoot            transform_component            <- player_movement_component goes HERE
├─ Mesh            <asset mesh class>             (mesh_component subclass from the Assets digest)
└─ CameraPivot     transform_component
   └─ Camera       perspective_camera_component
```

Package it as an Entity Prefab (`prefab_only`), place one instance, then wire the
device's `RigPrefabRoot : entity` editable to the placed rig root.

### The four moving parts

```verse
using { /Fortnite.com/Characters }
using { /Fortnite.com/Input/Character }   # Move, Jump, TraversalMapping
using { /Fortnite.com/Playspaces }
using { /Verse.org/Input }                # GetPlayerInput
using { /Verse.org/SceneGraph }
using { /Verse.org/Simulation }           # needed for @editable in a component
using { /Verse.org/SpatialMath }
using { /Fortnite.com/SceneGraphCameras } # fort_orbit_camera_modifier
```

**1. Input (42.10).** `Move : input_action(vector3)` and `Jump` live on
`TraversalMapping`. Nothing fires until the mapping is added per player:

```verse
if (PlayerInput := GetPlayerInput[P]):
    PlayerInput.AddInputMapping(TraversalMapping)
    MoveSub := PlayerInput.GetInputEvents(Move).TriggerActivationEvent.Subscribe(OnMove)
    MoveEnd := PlayerInput.GetInputEvents(Move).EndDetectEvent.Subscribe(OnMoveEnd)
    JumpSub := PlayerInput.GetInputEvents(Jump).TriggerActivationEvent.Subscribe(OnJump)
```

Payloads must match exactly: `Move`'s trigger is `tuple(player, vector3)` (stick /
WASD axes, -1..1 in `Forward`/`Left`), its `EndDetectEvent` is
`tuple(player, float)` (**no position** — zero the input there), `Jump`'s trigger
is `tuple(player, logic)`. Keep every `cancelable` per player and cancel on leave.

**2. Per-frame integration.** `TickEvents.PrePhysics.Subscribe` is **not**
available to creator code on 42.10 — `execution_listenable` is
`class<epic_internal>`, so subscribing fails with "Invalid access of internal
function". The hook you do have is `OnSimulate` plus your own delta clock:

```verse
OnSimulate<override>()<suspends> : void =
    var Last : float = GetSimulationElapsedTime()
    loop:
        Sleep(0.0)                      # exactly one frame
        if (not IsSimulating[]):
            break
        Now := GetSimulationElapsedTime()
        Step(Now - Last)
        set Last = Now
```

Then move the entity with `Entity.GetGlobalTransform()` /
`Entity.SetGlobalTransform(transform{...})` — global, not local, or a parented rig
drifts (`movement_transforms`).

**3. Orbit camera.** Install `fort_orbit_camera_modifier` on the rig's camera and
hand that camera to the player's director:

```verse
if (Cam := (for (C : RigPrefabRoot.FindDescendantComponents(perspective_camera_component)) do C)[0]):
    Orbit := fort_orbit_camera_modifier:
        TargetEntity := RigPrefabRoot
    set Orbit.CameraDistanceCentimeters = 450.0
    set Orbit.CameraHeightCentimeters = 120.0
    set Orbit.EnableCollision = true
    OrbitHandle := Cam.CameraModifiers.AddModifier(Orbit, VisualModifierPosition)   # parens!
    if (Director := (for (D : P.FindDescendantComponents(camera_director_component)) do D)[0]):
        if (CamHandle := Director.AddCamera[Cam, 100]) {}                            # brackets!
```

`AddModifier` has no `<decides>` (parens); `AddCamera` has it (brackets). Full
field table and the transition/blend API: `cameras`.

**4. Park the stock character** so Fortnite movement and your integrator don't
both drive the view:

```verse
if (FC := P.GetFortCharacter[]):
    FC.PutInStasis(stasis_args{})
    FC.Hide()
```

Undo with `ReleaseFromStasis()` when handing control back.

### The tuning surface

`player_movement_component` exposes these as `@editable var`s — this is the whole
point of rolling your own:

| Editable | Default | Meaning |
|---|---|---|
| `MaxSpeed` | 600.0 | cm/s planar cap |
| `Acceleration` | 3000.0 | cm/s² while the stick is held |
| `Friction` | 2000.0 | cm/s² deceleration on release |
| `Gravity` | -1800.0 | cm/s² (negative = down) |
| `JumpImpulse` | 700.0 | instantaneous Up velocity |
| `GroundHeight` | 0.0 | flat-ground plane; swap for a downward sweep on real terrain |

`GroundHeight` is deliberately the simple version. For real terrain, replace the
height test with a downward `FindSweepHits` probe (see the virtualpointer skill's
`screenspace_trace` for the sweep call shape) and use the hit's contact height.

### Gotchas that cost a compile each

| Symptom | Cause | Fix |
|---|---|---|
| `3506 Unknown identifier 'editable'` in a component file | `@editable` comes from `/Verse.org/Simulation` | add that `using` |
| `3512` on `OnGround := Pos.Up <= GroundHeight` | comparisons are `<decides>`; they need a failure context | `var OnGround : logic = false` then `if (Pos.Up <= …): set OnGround = true` |
| `3511` / `3513` on the modifier line | `AddModifier` is not `<decides>` | parens, not brackets |
| `3511` on the camera line | `AddCamera` **is** `<decides>` | brackets, and put it in an `if` |
| "Invalid access of internal function" on a tick subscribe | `execution_listenable` is `epic_internal` | `OnSimulate` + `Sleep(0.0)` |
| `3588` on a local named like a method | local shadowed the component's `Step` | rename the local |
| Rig teleports back each frame | stock character still driving | `PutInStasis` + `Hide` |

### Verify

1. `workspace_compile_verse` → 0 errors (2304 warnings expected).
2. Launch a session: the camera should sit behind the rig at
   `CameraDistanceCentimeters`, and WASD/stick should move the **rig**, not a
   Fortnite character.
3. Jump: apex should scale with `JumpImpulse` and fall rate with `Gravity` —
   if it doesn't, your delta clock isn't advancing (check `IsSimulating[]`).
4. Second player joins → they get their own component instance and camera claim.

### Don'ts

- Don't promise a publishable island — this is Experimental end to end.
- Don't drive the rig from the device tick; put the integrator on the entity.
- Don't skip `AddInputMapping(TraversalMapping)` — no mapping, no `Move` events.
- Don't read a position out of `Move`'s `EndDetectEvent` — it carries only a float.
- Don't leave a player's `cancelable`s uncancelled on leave (camera stays claimed).
- Don't mix the two `vector3` families — SpatialMath (Forward/Left/Up) here.

### Related

- Camera API detail → `cameras`
- Component lifecycle / hierarchy queries → `verse_authoring`
- Global vs local transforms → `movement_transforms`
- Prefab packaging → `prefab_only`
- Input actions catalog → `skill_read_subskill("verse", "sys_input_devices")`
