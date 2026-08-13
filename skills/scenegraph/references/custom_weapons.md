---
description: "Custom Scene Graph Armory weapons — Entity Prefab templates (AR/pistol/shotgun/SMG), fort_trace_weapon_component tuning, mesh/collision/pivot, world pickup without Verse, and creative_device grant/equip/clear/mutate/has via tags"
metadata:
  order: 7
  label: "Custom Armory weapons"
  default_enabled: false
  load_condition: "Creating a custom player weapon prefab, Armory assault_rifle_template / pistol / shotgun / SMG, fort_trace_weapon_component, granting or clearing custom guns in inventory, SetDamage/SetFireRate on custom weapons, or Verse tags on weapon prefabs"
---

# Custom Armory weapons (Scene Graph)

Custom player firearms are **Entity Prefabs** from `/Fortnite.com/Armory`, not
hand-rolled raycasts and not stock `/Fortnite.com/Weapons` classes. The UI may
say “forge”; digests say `fort_trace_weapon_component`. Always confirm members
with `get_verse_api` / `search_verse_digest` before shipping.

## Choose the path

| Goal | Load |
|------|------|
| Stock Fortnite gun grant / pickup | `skill_read_subskill("scenegraph", "itemization")` |
| **Custom mesh + tunable AR/pistol/shotgun/SMG** | **this file** |
| Custom non-weapon item (pickup / icon / mesh) | `skill_read_subskill("scenegraph", "custom_items")` |
| Soft persist bags + Creative Item Granter | `skill_read_subskill("verse", "sys_inventory")` |
| NPC combat / projectiles | Store `npc-ai` / `sys_npc_ai` |
| Cosmetic weapon on NPC skeleton | `skill_read_subskill("animation", "npc_items")` |

**No Verse required for loot on the ground.** Drag the prefab into the level;
the player walks up and picks it up. Verse is only for grant / equip / clear /
mutate / has-check.

## Project gates

1. **Project Settings → Custom Items in Inventory** = true (same family as
   custom items).
2. Optional / experimental: **Scene Graph Animation** — skeletal meshes in
   Scene Graph + Verse play API for bolt/slide motion. Same publish risk as
   other experimental Scene Graph animation — islands using it may not publish;
   prefer **static** meshes unless you need weapon animation.
3. Island **itemization inventory configuration** must be set or the hotbar
   stays empty after a successful grant — see
   `skill_read_subskill("islandsettings", "recipes")` (same gotcha as
   `itemization`).

## Author the prefab

Content Drawer → right-click → **Entity Prefab** → switch **template** → pick
one of four Armory templates (more may arrive later):

| Template (digest) | Typical use |
|-------------------|-------------|
| `assault_rifle_template` | AR / custom rifle |
| `pistol_template` | Sidearm |
| `shotgun_template` | Shotgun |
| `sub_machine_gun_template` | SMG |

Name the asset (e.g. `GnomeGun`). You are in the prefab editor with the entity
and its components. Templates already ship a full fire/reload loop — you tune
and re-skin them.

### Component tour (UI → digest)

**Pickup** — `fort_item_pickup_interactable_component`
(`/Fortnite.com/Itemization`, extends `basic_interactable_component`).
Gated `@available {MinUploadedAtFNVersion := 4040}`. Owning entity must have
`item_component` **and** `mesh_component`. Fields from
`basic_interactable_component`:

- `CanInteractMessage` / `CannotInteractMessage`
- `Cooldown` / `CooldownPerAgent`
- `SuccessLimit` / `InteractableDuration`
- `Enable()` / `Disable()` (and item-interaction enable helpers)

**Weapon settings** — `fort_trace_weapon_component` (`/Fortnite.com/Armory`).
UI groups map to digest properties (all have matching `Set*` Verse APIs —
Ctrl+click the type in the Verse editor to open the digest):

| UI group | Properties (confirm with `get_verse_api`) |
|----------|------------------------------------------|
| Damage | `Damage`, `EnvironmentalDamageMultiplier`, `RangeDamageMultiplier` (`[]fort_range_damage_multiplier` falloff) |
| Shots | `MaxRange`, `FireRate`, `ReloadTime` |
| Spread | `ExpansionRateMultiplierPerShot`, `CooldownRateMultiplierOverTime`, idle/moving/crouch/slide/sprint/ADS spread multipliers |
| Recoil | `RecoilMultiplier`, `AimDownSightRecoilMultiplier` |
| Ammo | `MagazineCapacity`, `ShotAmmoCost` (no separate reserve-ammo setter on this component) |
| Visuals | `MuzzleFlash`, `MuzzleOffset`, `BulletTracer` (Niagara), `EjectionPortOffset`, `BulletShells` |
| Sounds | `WeaponFireSound`, `EquipSound` (UI “clip”), ADS start/end, reload start/insert/end, `OutOfAmmoSound` |

**UI clamps (editor):** FireRate max **25** (typing 100 clamps); Recoil max
**10**.

**Base weapon** — `fort_weapon_component`: `IsHolstered`, `HolsterChangedEvent`.

**Presentation** — `rarity_component`, `description_component` (display name +
flavor), `icon_component` (hotbar). Icon tips: Texture Source Actions to resize;
use a **transparent PNG** so rarity color shows through behind the art.

**Item categories** — optional `weapon_ranged` / melee on `item_component`.
Melee category exists but is undemonstrated — treat as unknown.

**Mesh flags** — after assigning your mesh: Enabled / Collidable / Visible (and
related mesh flags). Transform component: leave default.

## Custom mesh pipeline

1. **Sources:** Sketchfab, Fortnite Porting → Blender, Meshy, etc.
2. Prefer a **static** mesh for non-animated guns. Sculpted/skeletal only if you
   enable experimental Scene Graph Animation.
3. **Pivot on the handle** in Blender (grip = character attach point).
4. Optional: join multi-part meshes (gun + prop); export FBX as mesh with
   **Apply Transform**.
5. **Textures:** Fortnite Porting often lands textures under a Texture Paints /
   cache folder — copy that path from the file explorer and import into a
   project `Textures` folder.
6. Create materials (packed ORM/specular maps → pin **G / R / B** into the
   matching material inputs; set material **Usage** for static mesh /
   instance / skeletal as needed). Cross-link materials skill for graph details.
7. Assign materials **per mesh material slot** (e.g. slot 0 = gun body, slot 1 =
   prop / gnome).
8. **Collision (Epic docs criteria):** Collision Preset → **Overlap All**;
   generate collision if missing (e.g. simplified box); delete stray hulls;
   customize as needed. Pivot must stay on the handle.
9. Wrong pivot after import: place the static mesh in the level → **Modeling
   Mode → XForm → Edit Pivot → Accept**. New instances use the new pivot.
10. **Prefab mesh swap (hard rule):** the template mesh slot is not swappable
    in place. **Delete** the stock mesh component, **add** a new
    `mesh_component` (asset-generated — needs a project mesh asset). The mesh
    class only appears after **Assets digest / Verse compile**. If the picker
    is empty, compile Verse and try again.

Cross-links: `modeling`, `materials`, optional `blender` / meshy; Niagara
muzzle/tracer → `vfx`.

## World use and variants

- Drag the Entity Prefab into the level for world loot (pickup can feel iffy).
- Verify look in **free camera** (third person) before trusting first person —
  first person is often bugged for custom Armory meshes.
- Scene Graph is modular: **Alt+drag** placed instances and tune FireRate /
  MagazineCapacity / Recoil on the **instance** (does not rewrite the prefab
  asset). Respect UI clamps above.
- Players can hold **multiple copies** in one inventory.
- Infinite magazine is a **playtest / island cheat**, not an Armory property.

## Verse tags

```verse
using { /Verse.org/Simulation/Tags }

my_gun_tag := class(tag):
```

Apply via **Edit Tags** on placed entities and/or on the **prefab asset**, then
save the prefab so instances inherit. Use separate tag classes per gun family.
Query with `FindDescendantEntitiesWithTag` (see
`skill_read_subskill("scenegraph", "verse_authoring")`) plus inventory
`FindItems` for clear / has / mutate-all.

## Verse controller (`creative_device`)

Not an entity component — a placed Creative Verse device with button
`@editable`s.

Modules (typical):

```verse
using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/Armory }
using { /Fortnite.com/Itemization }
using { /UnrealEngine.com/Itemization }
using { /Verse.org/SceneGraph }
using { /Verse.org/Simulation }
using { /Verse.org/Simulation/Tags }
using { /UnrealEngine.com/Temporary/Diagnostics }
using { /Verse.org/Assets }   # project prefab class after compile
```

After Verse build, the prefab becomes a concrete entity class in
Assets.digest (e.g. `GnomeGun{}` — name follows your asset path). Construct a
**fresh** instance per grant; never reuse one entity across players.

### Editables

- Five `button_device`s: Grant, ChangeStats, Equip, Has, Clear
- Grant-time `Damage` / `FireRate`
- Change-to `Damage` / `FireRate` (second pair)
- Per-player `[player]logic` map for holster-watch once

Wire in `OnBegin`: subscribe all buttons + `PlayerRemovedEvent`; remove the
player from the watch map on leave (avoids leaks). Guard holster-watch spawn
so it does not run twice (known double-print bug).

### Five operations

1. **Grant** — inventory helper → construct prefab →
   `GetComponent[fort_trace_weapon_component]` / FindDescendant →
   `SetDamage` / `SetFireRate` from grant editables → `AddItemDistribute` →
   on success `item_component.Equip()` + start holster watch once; on failure
   `RemoveFromParent()`.
2. **Change stats** — every tagged gun in inventory →
   `SetDamage` / `SetFireRate` from change-to editables.
3. **Equip** — tagged item already in inventory → `Equip()`.
4. **Has** — tagged find → `Print` true/false.
5. **Clear** — tagged find (or inventory `FindItems` + tag filter) →
   `RemoveItem` each.

Tip: **Ctrl+click** a component type in the Verse editor to jump to its digest
API (all Scene Graph setters for the weapon live there).

### Compiling skeleton (confirm names before ship)

Replace `GnomeGun` / `my_gun_tag` with your Assets.digest / tag names after
compile. Prefer `case` on `result` types — confirm with digests if your build
uses a different unwrap.

```verse
using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/Armory }
using { /UnrealEngine.com/Itemization }
using { /Verse.org/SceneGraph }
using { /Verse.org/Simulation }
using { /Verse.org/Simulation/Tags }
using { /UnrealEngine.com/Temporary/Diagnostics }
using { /Verse.org/Assets }

my_gun_tag := class(tag):

# Epic-style helper — inventory lives on a descendant of the agent.
GetFirstInventory(Agent:agent)<transacts><decides>:inventory_component =
    (for (Inv : Agent.FindDescendantComponents(inventory_component)) do Inv)[0]

custom_weapon_controller_device := class(creative_device):
    @editable GrantButton : button_device = button_device{}
    @editable ChangeButton : button_device = button_device{}
    @editable EquipButton : button_device = button_device{}
    @editable HasButton : button_device = button_device{}
    @editable ClearButton : button_device = button_device{}

    @editable GrantDamage : float = 30.0
    @editable GrantFireRate : float = 8.0
    @editable ChangeToDamage : float = 60.0
    @editable ChangeToFireRate : float = 16.0

    var IsWatching : [player]logic = map{}

    OnBegin<override>()<suspends>:void =
        GrantButton.InteractedWithEvent.Subscribe(OnGrant)
        ChangeButton.InteractedWithEvent.Subscribe(OnChangeStats)
        EquipButton.InteractedWithEvent.Subscribe(OnEquip)
        HasButton.InteractedWithEvent.Subscribe(OnHas)
        ClearButton.InteractedWithEvent.Subscribe(OnClear)
        GetPlayspace().PlayerRemovedEvent().Subscribe(OnPlayerRemoved)

    OnPlayerRemoved(Player:player):void =
        if (set IsWatching[Player] = false) {}

    OnGrant(Agent:agent):void =
        spawn{ GrantGun(Agent) }

    GrantGun(Agent:agent)<suspends>:void =
        if:
            Inventory := GetFirstInventory[Agent]
            Player := player[Agent]
        then:
            # Fresh prefab instance — name from Assets.digest after Verse compile.
            Gun := GnomeGun{}
            if (Trace := Gun.GetComponent[fort_trace_weapon_component]):
                Trace.SetDamage(GrantDamage)
                Trace.SetFireRate(GrantFireRate)
            AddResult := Inventory.AddItemDistribute(Gun)
            case (AddResult):
                Ok(Added) =>
                    for (Item : Added.AddedItems):
                        if (IC := Item.GetComponent[item_component]):
                            IC.Equip()
                    if (not IsWatching[Player]? or IsWatching[Player] = false):
                        if (set IsWatching[Player] = true) {}
                        spawn{ WatchHolster(Agent) }
                Err(_) =>
                    Gun.RemoveFromParent()

    OnChangeStats(Agent:agent):void =
        for (Gun : Agent.FindDescendantEntitiesWithTag(my_gun_tag)):
            if (Trace := Gun.GetComponent[fort_trace_weapon_component]):
                Trace.SetDamage(ChangeToDamage)
                Trace.SetFireRate(ChangeToFireRate)

    OnEquip(Agent:agent):void =
        for (Gun : Agent.FindDescendantEntitiesWithTag(my_gun_tag)):
            if (IC := Gun.GetComponent[item_component]):
                IC.Equip()

    OnHas(Agent:agent):void =
        Found := false
        for (Gun : Agent.FindDescendantEntitiesWithTag(my_gun_tag)):
            set Found = true
        if (Found = true):
            Print("Player has custom gun in inventory")
        else:
            Print("Player does not have custom gun")

    OnClear(Agent:agent):void =
        if (Inventory := GetFirstInventory[Agent]):
            for (Gun : Agent.FindDescendantEntitiesWithTag(my_gun_tag)):
                Inventory.RemoveItem(Gun)

    WatchHolster(Agent:agent)<suspends>:void =
        loop:
            for (Gun : Agent.FindDescendantEntitiesWithTag(my_gun_tag)):
                if (Weapon := Gun.GetComponent[fort_weapon_component]):
                    Weapon.HolsterChangedEvent.Await()
                    if (Weapon.IsHolstered = true):
                        Print("Gun holstered")
                    else:
                        Print("Gun unholstered")
            Sleep(0.1)
```

Notes:

- `GnomeGun` is a placeholder for your compiled prefab class — verify with
  `get_verse_api({"name": "GnomeGun"})` (or your asset name).
- Tag the **prefab** with `my_gun_tag` and save so grants carry the tag.
- `AddItemDistribute` / `RemoveItem` return `result` — not failable `if`
  wrappers; use `case` (or the unwrap your build documents).
- Holster watch: once per player via `IsWatching`; clean on `PlayerRemoved`.
- Wire buttons with `wire_verse_device_ref` after placing the device —
  **one field per turn** (`skill_read_subskill("uefn", "batch_commands")`).
  Never same-turn multi-wire.

## Limits and pitfalls

- First-person view often broken; verify in free camera / third person.
- Muzzle / ejection / FX offsets are hard to visualize in the prefab editor.
- Recoil feel can be subtle even at high multipliers.
- Pickup interaction can feel iffy.
- Scene Graph Animation for weapon skeletal motion is experimental / publish-risk.
- Infinite magazine ≠ Armory property (playtest cheat).
- UI “forge” names ≠ digest `fort_trace_*` — trust digests.

## Failure table

| Symptom | Cause |
|---------|-------|
| Mesh not in mesh_component picker | Assets digest stale — compile Verse |
| Gun floats beside the hand | Pivot not on handle — Edit Pivot / Blender |
| Cannot pick up | Collision not Overlap All; missing mesh/item components on pickup entity |
| Grant “works” but no hotbar icon | Island inventory configuration missing |
| Overlay/mutate hits nothing | Tag missing on prefab / instances |
| Gun left in world after failed grant | Forgot `RemoveFromParent` on add failure |
| Holster prints twice | Watch loop spawned twice — use `IsWatching` map |
| FireRate stuck at 25 | Editor UI clamp |
| First person looks wrong | Known limit — use third person |
| Island won’t publish after weapon anim | Experimental Scene Graph Animation enabled |

## Related skills / MCP (no new weapon tools)

| Need | Skill | Tools |
|------|-------|-------|
| This path | scenegraph `custom_weapons` | entity/prefab tools + Verse digests |
| Custom non-weapon items | scenegraph `custom_items` | same |
| Stock FN guns | scenegraph `itemization` | same |
| Soft inventory / shops | verse `sys_inventory` / `sys_economy` | device wire / granter fields |
| Mesh / mats / Niagara | modeling, materials, vfx | domain MCP tools |
| Tags / hierarchy | scenegraph `verse_authoring` | digests |
| Weapon inspect / melee clip on player | animation `player_animation` | `set_anim_additive_type`, etc. |
| NPC combat (not player Armory) | Store `npc-ai` / verse `sys_npc_ai` | digests |
| Flamethrower / hand-rolled fire loops | out of scope — sequel content, not Armory templates | — |
