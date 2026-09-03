---
description: "Scene Graph cameras — perspective/orthographic/physical camera components, camera_director_component.AddCamera, the camera_modifier stack (AddModifier has no <decides>), Fortnite fort_orbit / fort_fixed_angle / fort_fixed_point modifiers, enter/exit transitions and blends; all Experimental (blocks publishing)"
metadata:
  order: 11
  label: "Cameras & camera modifiers"
  default_enabled: false
  load_condition: "Scene Graph cameras, camera components, orbit camera, camera modifier, camera director, camera transitions/blends, following a custom entity with a camera, or a custom camera rig instead of the Fortnite gameplay camera"
---

## Scene Graph cameras & camera modifiers

> **Snippets here are fragments.** The `using` block in this file's first code
> block applies to all of them.

> **Everything on this page is `@experimental` and blocks publishing.** Every
> symbol below emits `Script warning 2304` and a project that uses one cannot be
> published. Say that to the user *before* building a camera rig.

```verse
using { /Verse.org/SceneGraph }        # camera components, modifier stack, positions
using { /Verse.org/Simulation }        # required for @editable in a component file
using { /Verse.org/SpatialMath }       # vector3 / rotation (LUF)
using { /Fortnite.com/SceneGraphCameras }   # fort_* camera modifiers
```

Everything here was read from the 42.10 digests and **compile-checked in UEFN**
(0 errors, warnings 2304 only).

### The camera components

`camera_component` is `class<final_super><abstract>(component, has_camera_modifier)`
— abstract, so you never place it directly; you query with it and you place one of
these concrete subclasses (all `@available {MinUploadedAtFNVersion := 4110}`):

| Component | Use | Key field |
|---|---|---|
| `perspective_camera_component` | normal gameplay camera | `FieldOfViewDegrees` |
| `orthographic_camera_component` | 2D / isometric / map views | `OrthographicProjectionWidth` |
| `physical_camera_component` | cinematic / physically accurate | `camera_body` + `camera_lens` (sensor mm, `FocalLengthMillimeters`, `FStop`, `SqueezeFactor`, `BladeCount`) |
| `camera_director_component` | picks the active camera and blends | `AddCamera` (below) |

On the base class (so on all of them): `var NearClippingPlaneDistance : float`
and `var FarClippingPlaneDistance : float` — both `@editable`; the docs' rule is
`<= 0.0` / `Inf` means "use defaults".

One component per class per entity, as everywhere in Scene Graph — so a rig that
needs two views needs two child entities.

### Making a camera the player's view — `camera_director_component`

```verse
# AddCamera IS <decides> -> square brackets.
# AddCamera<native><public>(Camera:camera_component, Priority:rational)<transacts><decides>:cancelable
if:
    Director := (for (D : Player.FindDescendantComponents(camera_director_component)) do D)[0]
    Cam := (for (C : RigRoot.FindDescendantComponents(perspective_camera_component)) do C)[0]
    Handle := Director.AddCamera[Cam, 100]
then:
    Print("custom camera active")
```

Highest `Priority` wins. The returned `cancelable` is how you give the view back
— hold it per player and `Cancel()` it on leave/teardown.

### Camera modifiers — the orbit camera the ecosystem talks about

A modifier mutates the final `camera_state` (render location/rotation, projection,
body/lens, clip planes) without moving any camera entity. `camera_state` itself is
`class<computes><epic_internal>` — **you cannot construct one**, so writing your
own `camera_modifier` from scratch is not available to creator code. Use the
Fortnite-supplied ones.

Every `camera_component` implements `has_camera_modifier`, which exposes:

```verse
CameraModifiers<public> : modifier_stack(camera_state)
```

and the stack's API is:

```verse
# AddModifier has NO <decides> -> PARENTHESES, not brackets. Returns cancelable.
# AddModifier<public>(Modifier:modifier(t), Position:rational)<transacts>:cancelable
Handle := Cam.CameraModifiers.AddModifier(Orbit, VisualModifierPosition)
...
Handle.Cancel()                                   # removes it from the stack
```

Calling it `AddModifier[...]` is the mistake to avoid: it yields
`Script error 3511` (square brackets on a non-`decides` function) and then `3513`.
Position constants live in `/Verse.org/SceneGraph`: **`GlobalModifierPosition`**
and **`VisualModifierPosition`** (both `rational`). Modifiers evaluate in position
order; same position = most recently added evaluates last. `FirstPosition` /
`LastPosition` are also readable on the stack.

#### `fort_orbit_camera_modifier` (`/Fortnite.com/SceneGraphCameras`)

`class<concrete>(camera_modifier)`, `@available {MinUploadedAtFNVersion := 4200}`
— i.e. **42.00+**, and Experimental. `TargetEntity` is not a `var`, so it is set
at construction; everything else is a `var` you can retune live.

```verse
Orbit := fort_orbit_camera_modifier:
    TargetEntity := RigRoot                       # entity the camera orbits
set Orbit.CameraDistanceCentimeters = 450.0       # boom length along forward
set Orbit.CameraHeightCentimeters = 120.0         # pivot height above the entity root
set Orbit.EnableCollision = true                  # camera-to-world collision avoidance
set Orbit.CollisionSphereRadiusCentimeters = 20.0
```

Full field list (all cm / all `var` unless noted):

| Field | Meaning |
|---|---|
| `TargetEntity : entity` (not `var`) | entity the camera is attached to |
| `BoomArmOffsetCentimeters : vector3` | boom offset relative to the entity |
| `BoomArmMaxForwardInterpolationFactor` / `...BackwardInterpolationFactor` | boom interpolation clamps |
| `ForwardDampingFactor`, `LateralDampingFactor`, `VerticalDampingFactor` | per-axis follow damping |
| `EnableCollision : logic`, `CollisionSphereRadiusCentimeters` | collision avoidance |
| `CameraDistanceCentimeters` | camera → orbit pivot along forward |
| `CameraHeightCentimeters` | pivot height above the entity root |
| `PositionOffsetCentimeters : vector3` | offset applied after the boom arm |
| `RotationOffset : rotation` | orientation offset |

Siblings in the same module, same version gate and shape:

- **`fort_fixed_angle_camera_modifier`** — `TargetEntity`, `CameraDistanceCentimeters`,
  `PositionOffsetCentimeters`, `RotationOffset`, the three damping factors,
  `EnableCollision`, `CollisionSphereRadiusCentimeters`,
  `CollisionSafePositionOffsetCentimeters`. Fixed-angle chase / isometric follow.
- **`fort_fixed_point_camera_modifier`** — `RotationOffset` (+ its own fields);
  a camera pinned to a point that looks around.

`vector3` / `rotation` here are `/Verse.org/SpatialMath` (Forward/Left/Up) — not
the Temporary XYZ family. Mixing them is `movement_transforms`' classic bug.

### Transitions and blends (working from 42.10)

Subclassing a **concrete** camera component in creator Verse is legal — verified
by compile — so transitions are authored by overriding on your own subclass:

```verse
my_cam := class<final_super>(perspective_camera_component):
    GetEnterTransition<override>(SourceCamera : camera_component)<transacts><decides> : camera_transition =
        camera_transition{Blend := camera_mode_blend_smoothstep{}, Duration := 0.5}

    GetExitTransition<override>(DestinationCamera : camera_component)<transacts><decides> : camera_transition =
        camera_transition{Blend := camera_mode_blend_pop{}, Duration := 0.0}
```

Both hooks are `<transacts><decides>`. Blends (all `<concrete>`, all Experimental):
`camera_mode_blend_pop{}` (instant cut), `_linear`, `_smoothstep`, `_smootherstep`,
`_orbit{DrivingBlend := …}`. `camera_transition_initial_orientation` picks what the
new camera inherits: `PreviousYawPitch`, `PreviousAbsoluteTarget`,
`PreviousRelativeTarget`.

### Custom meshes on a camera rig (or any entity)

`mesh_component` is `class<final_super><epic_internal>(component, enableable)` —
**you cannot subclass it in creator Verse.** Importing a mesh generates the
subclass for you in the project's Assets digest, e.g.
`SM_Hat01_Cap := class<final>(mesh_component)` under a `<scoped {…}>` module.
So "custom mesh" means: import the asset, then reference the generated class.

```
list_verse_types(digest="assets", name_filter="SM_")   # find the generated classes
get_verse_api("<ClassName>")                            # confirm module + members
```

Add it to an entity as an asset component through Epic `EntityToolset.AddComponent`
(`editor_tools` covers class resolution); in Verse you query it with
`Entity.GetComponent[mesh_component]` and toggle it via `enableable`.

### Verify

1. `workspace_compile_verse` — expect **0 errors** and only 2304 warnings. The
   offline LSP alone will not prove a camera rig builds.
2. Launch a session; the rig camera should take over on join (`Print` in the
   `AddCamera` success branch).
3. Retune `CameraDistanceCentimeters` / `CameraHeightCentimeters` live and
   re-enter the session rather than guessing numbers.

### Don'ts

- Don't call `AddModifier[...]` with brackets — no `<decides>` (error 3511/3513).
- Don't call `AddCamera(...)` with parens — it **is** `<decides>`. Error 3511 covers
  both directions (compile-verified): "uses parentheses to call a function that has
  the 'decides' effect" and "uses square brackets to call a function that does not".
- Don't try to author a `camera_modifier` subclass that builds a `camera_state` —
  `camera_state` is `epic_internal`.
- Don't subclass `mesh_component`, and don't invent mesh class names — read them
  from the Assets digest.
- Don't promise publishing: every symbol on this page is Experimental.
- Don't place two components of the same camera class on one entity.

### Related

- Full player controller recipe → `skill_read_subskill("scenegraph", "custom_player_controller")`
- Component lifecycle → `verse_authoring`
- Why the rig doesn't move → `movement_transforms`
- Component catalog → `components`
