---
description: "Custom Scene Graph items that can do anything — Entity Prefab itemization shell + Verse components for equipped logic, KFM visuals, categories/stack/rarity, world loot, and creative_device grant/equip/clear/has"
metadata:
  order: 8
  label: "Custom Scene Graph items"
  default_enabled: false
  load_condition: "Creating a fully custom non-weapon item Entity Prefab, custom inventory pickup mesh/icon, item Categories (currency/resource/ammo), stacking/rarity, spinning or bobbing dropped items with keyframed_movement, detecting IsEquipped / ChangeEquippedEvent, Verse components that run while held, or granting custom Scene Graph items (not Armory weapons)"
---

# Custom Scene Graph items (do anything)

Custom non-weapon items are **Entity Prefabs**: an itemization **shell** plus
**your Verse components** for all gameplay. There is no separate “custom item
device type.” Behavior = whatever you attach and run while the entity is
simulating / equipped. Always confirm members with `get_verse_api` /
`search_verse_digest` before shipping.

**UEFN + Scene Graph only** — not Fortnite Creative 1.0. Custom items require
the Scene Graph / inventory stack; they do not exist as Classic Creative
devices.

Not Creative Item Granters / Item Spawners. Not Armory weapon templates
(`custom_weapons`).

## Choose the path

| Goal | Load |
|------|------|
| Stock Fortnite gun / item grant | `skill_read_subskill("scenegraph", "itemization")` |
| **Fully custom non-weapon item (mesh/icon + Verse logic)** | **this file** |
| Template ability (Spicy Sprint / AbilityElements / IA_Sprint) | `skill_read_subskill("scenegraph", "template_abilities")` |
| Custom Armory firearm (AR/pistol/shotgun/SMG) | `skill_read_subskill("scenegraph", "custom_weapons")` |
| Soft persist bags + Creative Item Granter | `skill_read_subskill("verse", "sys_inventory")` |

**No Verse required for loot on the ground.** Place the prefab; the player
picks it up. Verse is for grant / equip / equipped gameplay / KFM drivers /
anything else you invent.

## Mental model — shell + behavior

```
Entity Prefab (item entity)
├── itemization shell (required builtins)
│   ├── item_component          (+ optional Categories)
│   ├── fort_item_pickup_interactable_component
│   ├── description_component   (Name / Description / ShortDescription)
│   ├── icon_component          (Icon:texture)
│   └── mesh_component          (dropped look; Collidable = false)
├── optional builtins
│   ├── rarity_component
│   ├── basic_stackable_component
│   └── keyframed_movement_component   (visuals while dropped)
└── YOUR Verse components          ← this is "do anything"
    ├── equipped detect / while-held loops
    ├── buttons, VFX, damage, economy hooks, …
    └── KFM drivers, tags, child entities
```

**Do not** put `fort_inventory_component` / `fort_inventory_*` on the item.
Tutorials often add “Fort Inventory” in the Add Component list — those types
are **player inventory** subclasses under `/Fortnite.com/Itemization` (they
define hotbars/tabs the *agent* owns), not item shells:

| Player inventory type (do NOT put on the item) |
|------------------------------------------------|
| `fort_inventory_component` (base) |
| `fort_inventory_weapon_hotbar_component` |
| `fort_inventory_build_hotbar_component` |
| `fort_inventory_harvest_tool_component` |
| `fort_inventory_trap_component` |
| `fort_inventory_resources_component` |
| `fort_inventory_ammo_component` |
| `fort_inventory_currencies_component` |

Tab placement for *your* item uses `item_component.Categories` (below).

## Project gates

1. **Project Settings → Inventory system / Custom Items in Inventory** = true.
   Enabling inventory often flips related **experimental** Scene Graph options —
   publish-risk until Epic stabilizes.
2. Island **itemization inventory configuration** must be set or HUD stays empty
   after pickup/grant — `skill_read_subskill("islandsettings", "recipes")`.
3. Expect the **new inventory UI** (BR-style tabs) when Custom Items are on —
   that HUD is what surfaces custom currencies / resources / ammo / world items.

## Author the prefab

Content Drawer → right-click → **Entity Prefab** / **Entity Prefab Definition**
(blank / no Armory template). Prefab Scene Graph outliner: **simulation
entity** = world shell; your **item entity** is the child that gets components
(not the Fortnite Creative “prefab” kit concept — different word, same Epic
UI name). Prefab-owned edits → **Save the EntityPrefab** (`prefab_only` — MCP
cannot see prefab editor tabs).

MCP path: `create_empty_prefab` → edit comps in UEFN UI → Save →
`instantiate_prefab` + `save_current_level`.

### Required shell (UI → digest)

| UI label (tutorial) | Digest component | Role |
|---------------------|------------------|------|
| Item | `item_component` | Marks entity as an item. Add a **Categories** element in Details when you need a tab. |
| Fort item pickup | `fort_item_pickup_interactable_component` | World pickup/drop. **Do not skip** — tutorials forget this and pickups break. Needs sibling `item_component` + `mesh_component`. Gated FN ≥ 4040. |
| Item details | `description_component` | `Name`, `Description`, `ShortDescription` (`message`). Short copy is the interact / hover prompt before pickup. |
| Item icon | `icon_component` | `Icon:texture` — transparent PNG so rarity color shows through. |
| Mesh | `mesh_component` | **Dropped** appearance only for now (held mesh not reliable). **Collidable = false**. |

### Categories (inventory tabs)

`using { /Fortnite.com/Itemization/FortniteItemCategories }` — set on
`item_component.Categories` (Details → Categories → add element):

| Category | Typical tab / use |
|----------|-------------------|
| `WorldItem` | Generic world / custom item |
| `Currency` | Currency tab |
| `Resource` | Resources tab |
| `Ammo` | Ammo tab |
| `Trap` | Traps |
| `WeaponMelee` / `WeaponRanged` | Weapon tabs (prefer Armory templates for real guns → `custom_weapons`) |

Currency/resource/ammo-only items belong on those categories so they land in
the matching inventory UI tab, not the weapon hotbar.

### Optional builtins (digest-confirmed)

| Component | API notes |
|-----------|-----------|
| `rarity_component` | `var Rarity:rarity` — one rarity per entity. Instances in `/Fortnite.com/Itemization/FortniteRarities` (`Common` … `Exotic`). Gated FN ≥ 4000. |
| `basic_stackable_component` | Extends `stackable_component`: `StackSize`, `MaxStackSize`, `SetStackSize`, `SetMaxStackSize`, `Split`, `CanMergeInto`, `MergeInto`, stack change events. Set `split_prefab_type` to your prefab class. Grant with `?AllowMergeItems := true`. Gated FN ≥ 4000. |
| `keyframed_movement_component` | Dropped spin / bob / scale — drive from a Verse component (`movement_transforms`). |

## Custom mesh / icon pipeline

1. Import texture + static mesh under the **project** mount
   (`get_project_info().content_root` — never invent `/Game/...` creates).
2. **Verse build / push Verse changes** so Assets digest exposes mesh classes
   for Scene Graph — without this the mesh picker stays empty.
3. Assign icon on `icon_component`; for mesh: **delete** the stock/cube
   `mesh_component`, **add** a new one with your project mesh (hard rule —
   in-place swap often fails).
4. Scale the mesh down in the prefab so the interact volume feels right. Weird
   hitbox after import → re-import / rescale.
5. Collidable **off** — collision on bumps / launches the player.

Cross-links: `modeling`, `materials`; optional `blender` / meshy.

## World use

- Save the Entity Prefab, then Content Browser drag or `instantiate_prefab` +
  `save_current_level`.
- **Creative Item Granters / Item Spawners do not accept custom Entity Prefab
  items yet** — world place or Verse grant only.
- Experimental bugs to expect (do not thrash the prefab trying to “fix” them):
  - Mesh **scale resets** after reassignment
  - Dropped item **flies / launches** oddly
  - **Icon breaks** after drop → re-pickup
  - Interact volume / hitbox feels wrong until re-import
- Prefer third-person / free camera for look checks.

## Dropped visuals (KFM)

Same Scene Graph motion path as any entity —
`skill_read_subskill("scenegraph", "movement_transforms")`.

1. Add builtin `keyframed_movement_component` on the item entity (leave defaults
   — do not subclass; class is `<final>`).
2. Verse Explorer → **Add new Verse file → Scene Graph component** (e.g.
   `keyframed_movement_cycle`). Build / push — the class only appears under
   Add Component after Verse succeeds.
3. Driver pattern:

```verse
using { /Verse.org/SceneGraph }
using { /Verse.org/SceneGraph/KeyframedMovement }
using { /Verse.org/SpatialMath }   # for typed deltas / axes when authoring in Verse
using { /Verse.org/Simulation }

keyframed_movement_cycle_component := class<final_super>(component):
    @editable
    Keyframes : []keyframed_movement_delta = array{}

    OnBeginSimulation<override>():void =
        (super:)OnBeginSimulation()
        if (KFM := Entity.GetComponent[keyframed_movement_component]):
            KFM.SetKeyframes(Keyframes, loop_keyframed_movement_playback_mode{})
            KFM.Play()

    OnEndSimulation<override>():void =
        if (KFM := Entity.GetComponent[keyframed_movement_component]):
            KFM.Stop()
        (super:)OnEndSimulation()
```

4. Prefab Details → add the Verse driver → fill the `@editable` keyframe array.
   For a ground spin: translation = 0; rotate on the **middle / yaw** axis
   (tutorial “yellow” gizmo); **≤ ~90° per keyframe** (360° single steps often
   fail). Four × 90° @ ~0.5s each ≈ 2s loop. Same API for bob (translation) or
   pulse (scale) — deltas are additive.
5. Always `Stop()` in `OnEndSimulation` — Scene Graph leaks crash sessions.

Playback: `oneshot_`, `loop_`, `pingpong_keyframed_movement_playback_mode`.
`SetKeyframes` does **not** autoplay — call `Play()`. Pick up → drop again
should keep spinning if the driver restarts on simulate.

## Do anything — Verse behavior on the item

Attach one or more **project Verse components** to the item entity. That is the
entire custom-ability surface: print, spawn VFX, open UI, spend currency, deal
damage, enable a button device via events, TickEvents for per-frame while held,
tags for FindDescendant queries, child entities for lights/meshes.

Lifecycle: subscribe in `OnBeginSimulation`, cancel in `OnEndSimulation`
(`verse_authoring`). Components simulate in editor and play — guard with
equipped checks if logic should only run when held.

### Equipped detect (digest names)

On `item_component`:

| API | Notes |
|-----|-------|
| `IsEquipped[]` | Failable succeeds when equipped |
| `ChangeEquippedEvent` | `listenable(change_equipped_result)` |
| `Equip()` / `Unequip()` | `result(...)` — not failable `if` |
| `Drop[]` / `PickUp[Inventory]` | World ↔ inventory |
| `ChangeInventoryEvent` | Inventory moves |

On `change_equipped_result` (event payload):

| Field | Type |
|-------|------|
| `ItemComponent` | `item_component` |
| `IsItemEquipped` | `logic` — this is the tutorial’s “Is Item Equipped” name |

Prefer `ChangeEquippedEvent` over polling. Polling recipe (tutorial style) must
break on `not IsSimulating[]` (on **this** `component`) to avoid memory leaks /
crashes when the item leaves the scene:

```verse
using { /UnrealEngine.com/Itemization }
using { /Verse.org/SceneGraph }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }

# Event-driven gate (preferred). A spawn task cannot be cancelled (task has no
# Cancel()), so the background loop races a stop signal instead.
custom_item_behavior_component := class<final_super>(component):
    var MaybeEquipSub : ?cancelable = false
    StopHolding : event() = event(){}

    OnBeginSimulation<override>():void =
        (super:)OnBeginSimulation()
        if (IC := Entity.GetComponent[item_component]):
            set MaybeEquipSub = option{ IC.ChangeEquippedEvent.Subscribe(OnEquipChanged) }
            if (IC.IsEquipped[]):
                StartHolding()

    OnEndSimulation<override>():void =
        StopHolding.Signal()
        if (Sub := MaybeEquipSub?):
            Sub.Cancel()
        set MaybeEquipSub = false
        (super:)OnEndSimulation()

    OnEquipChanged(Result:change_equipped_result):void =
        if (Result.IsItemEquipped = true):
            Print("Item is equipped")
            StartHolding()   # enable buttons / VFX / abilities here
        else:
            Print("Item is not equipped")
            StopHolding.Signal()    # disable the same logic here

    StartHolding():void =
        StopHolding.Signal()            # end any previous holder first
        spawn{ HoldUntilStopped() }

    HoldUntilStopped()<suspends>:void =
        race:
            StopHolding.Await()         # first to finish wins; the loop is cancelled
            WhileEquipped()

    WhileEquipped()<suspends>:void =
        # Prefer TickEvents.PrePhysics for per-frame work (verse_authoring).
        loop:
            if (not IsSimulating[]):
                break
            if (IC := Entity.GetComponent[item_component], IC.IsEquipped[]):
                # … your custom item logic …
                Sleep(0.1)
            else:
                break
```

`using { /UnrealEngine.com/Itemization }` is required for `item_component`.
Build / push Verse before the custom component appears in the prefab’s Add
Component list. The **gate** is `ChangeEquippedEvent` + `IsItemEquipped` (or
`IsEquipped[]`); cancellation is `race` against an `event()`, never `Cancel()` on
a `spawn` result.

### Agent-side inventory reactions

For systems outside the item (shops, quests, HUD): subscribe on the player’s
`inventory_component` to `AddItemEvent` / `RemoveItemEvent` / `EquipItemEvent` /
`UnequipItemEvent` — see `itemization`. Find inventory with
`Agent.FindDescendantComponents(inventory_component)`.

## Verse grant / equip / clear / has

Same helpers as `custom_weapons`. Tag the **prefab asset** and Save so grants
carry the tag.

```verse
using { /Fortnite.com/Devices }
using { /UnrealEngine.com/Itemization }
using { /Verse.org/SceneGraph }
using { /Verse.org/Simulation }
using { /Verse.org/Simulation/Tags }
using { /UnrealEngine.com/Temporary/Diagnostics }
using { /Verse.org/Assets }   # prefab class after compile

my_item_tag := class(tag):

GetFirstInventory(Agent:agent)<transacts><decides>:inventory_component =
    (for (Inv : Agent.FindDescendantComponents(inventory_component)) do Inv)[0]

custom_item_controller_device := class(creative_device):
    @editable GrantButton : button_device = button_device{}
    @editable EquipButton : button_device = button_device{}
    @editable HasButton : button_device = button_device{}
    @editable ClearButton : button_device = button_device{}

    OnBegin<override>()<suspends>:void =
        GrantButton.InteractedWithEvent.Subscribe(OnGrant)
        EquipButton.InteractedWithEvent.Subscribe(OnEquip)
        HasButton.InteractedWithEvent.Subscribe(OnHas)
        ClearButton.InteractedWithEvent.Subscribe(OnClear)

    OnGrant(Agent:agent):void =
        spawn{ GrantItem(Agent) }

    GrantItem(Agent:agent)<suspends>:void =
        if (Inventory := GetFirstInventory[Agent]):
            # Fresh prefab instance — name from Assets.digest after Verse compile.
            Item := MyCustomItem{}
            if (IC := Item.GetComponent[item_component]):
                Inventory.AddItemDistribute(Item)   # ?AllowMergeItems := true if stackable
                # result has no Ok/Err patterns — decide by parenting, same as custom_weapons
                if (IC.GetParentInventory[]):
                    IC.Equip()
                else if (IC.PickUp[Inventory]):
                    IC.Equip()
                else:
                    Item.RemoveFromParent()
            else:
                Item.RemoveFromParent()

    OnEquip(Agent:agent):void =
        for (Ent : Agent.FindDescendantEntitiesWithTag(my_item_tag)):
            if (IC := Ent.GetComponent[item_component]):
                IC.Equip()

    OnHas(Agent:agent):void =
        var Found : logic = false
        for (Ent : Agent.FindDescendantEntitiesWithTag(my_item_tag)):
            set Found = true
        if (Found = true):
            Print("Player has custom item")
        else:
            Print("Player does not have custom item")

    OnClear(Agent:agent):void =
        if (Inventory := GetFirstInventory[Agent]):
            for (Ent : Agent.FindDescendantEntitiesWithTag(my_item_tag)):
                Inventory.RemoveItem(Ent)
```

Rules:

- Construct a **fresh** prefab `{}` per grant — never reuse across players.
- `AddItemDistribute` / `RemoveItem` / `Equip` return `result` — use `case`.
- On add failure: `RemoveFromParent()`.
- Replace `MyCustomItem` after compile —
  `get_verse_api({"name": "MyCustomItem"})`.
- **Footgun:** bulk-granting many stock weapons + custom items in one tight
  loop has produced infinite-loop Verse errors. Grant one item per interaction.
- Wire buttons with `wire_verse_device_ref` — **one field per turn**
  (`skill_read_subskill("uefn", "batch_commands")`).

## Recipe checklist (full custom item)

1. Enable Custom Items / inventory + island inventory config.
2. `create_empty_prefab` / UI Entity Prefab → shell comps → Save prefab.
3. Import mesh/icon → Verse compile → assign; Collidable off.
4. Set `Categories` / `rarity_component` / `basic_stackable_component` as needed.
5. Write Verse behavior component(s) → build → add to prefab → Save.
6. Optional KFM + driver for dropped spin/bob.
7. Tag prefab; place in level and/or wire grant device.
8. PIE: pickup → equip → behavior → drop → cleanup (no leaks).

## Limits and pitfalls

- UEFN / Scene Graph only — not Creative 1.0.
- Experimental: drop flies, icon breaks on re-pickup, mesh scale resets, weird
  interact hitbox after import.
- Held / first-person mesh not reliable yet — dropped mesh for visuals.
- Creative granters / spawners cannot host custom Entity Prefab items yet.
- `fort_inventory_*` on the item is wrong — use `Categories` instead.
- KFM yaw steps above ~90° often fail; use multiple smaller deltas.
- Always `Stop()` KFM / cancel subs / break on `not IsSimulating[]` in
  `OnEndSimulation` — leaks crash sessions.
- Epic may ship more ability comps later — digests beat tutorials.

## Failure table

| Symptom | Cause |
|---------|-------|
| Mesh not in mesh_component picker | Assets digest stale — Verse build / push |
| Player bumps / launches the pickup | Mesh Collidable still true |
| Cannot pick up | Forgot `fort_item_pickup_interactable_component`, or missing `item_component` / `mesh_component` |
| Pickup works but HUD empty | Island inventory configuration missing |
| Item in wrong inventory tab | Missing / wrong `Categories` (or wrongly added `fort_inventory_*` on the item) |
| Component missing from Add Component | Verse not built / not pushed |
| Spin never starts | Forgot `Play()` after `SetKeyframes` |
| Spin / poll loop after despawn | Missing `OnEndSimulation` `Stop()` / `not IsSimulating[]` break |
| Logic runs when on ground | Forgot equipped gate (`IsItemEquipped` / `IsEquipped[]`) |
| Drop flies / icon broken / scale wrong | Known experimental bugs — re-place / re-import; do not over-tune |
| Grant crashes / infinite loop | Bulk grant loop — grant one at a time |
| Item left in world after failed grant | Forgot `RemoveFromParent` on add failure |
| Stacks never merge | Missing `basic_stackable_component` or `?AllowMergeItems := true` |

## Related skills / MCP (no new item tools)

| Need | Skill | Tools |
|------|-------|-------|
| This path | scenegraph `custom_items` | entity/prefab tools + Verse digests |
| Stock FN guns / items | scenegraph `itemization` | same |
| Custom Armory firearms | scenegraph `custom_weapons` | same |
| KFM / transforms / TickEvents | `movement_transforms`, `verse_authoring` | same |
| Soft inventory / shops | verse `sys_inventory` / `sys_economy` | device wire / granter fields |
| Mesh / mats / Niagara | modeling, materials, vfx | domain MCP tools |
| Tags / hierarchy | scenegraph `verse_authoring` | digests |
