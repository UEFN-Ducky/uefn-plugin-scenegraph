---
description: "Scene Graph itemization — item_component / inventory_component, granting Fortnite weapons from Verse, the trigger-driven item_granter_component, world pickups, dropping and equipping"
metadata:
  order: 6
  label: "Items, inventories & weapon granting"
  default_enabled: false
  load_condition: "Granting, spawning, dropping or equipping weapons and items, reading or filling a player inventory, building pickups/loot, or using item_component / inventory_component / fort_item_pickup_interactable_component"
---

## Items, inventories & granting weapons

**Weapons and items are entities, not devices.** Every Fortnite weapon is a
concrete `entity` class in the digests, so "spawn a weapon" is
`AssaultRifle_BR_CH4S1_Rare{}` — then you put that entity into an
`inventory_component`. Never `spawn_actor` a weapon class.

```verse
using { /Verse.org/SceneGraph }        # entity, component, FindDescendantComponents
using { /Verse.org/Simulation }        # agent (which IS an entity)
using { /Fortnite.com/Devices }        # trigger_device and friends
using { /Fortnite.com/Itemization }    # fort_item_pickup_interactable_component, rarities
using { /UnrealEngine.com/Itemization }  # item_component, inventory_component
```

Add `/Verse.org/SpatialMath` only when you place items in the world — and then
qualify transform types, because `/UnrealEngine.com` carries its own copies
(see `movement_transforms`).

### Mental model

- An **item** is an entity carrying an `item_component`.
- An **inventory** is an `inventory_component`, and on a player it lives on a
  **subentity** of the agent — not on the agent itself. That is why you search
  *descendants* rather than calling `GetComponent[inventory_component]`.
- `agent := class<unique><epic_internal>(entity)`, so every entity hierarchy
  query works directly on an agent. The other route to a player's entity is
  `Agent.GetFortCharacter[].GetEntity[]`.

### `inventory_component` (`/UnrealEngine.com/Itemization`)

| Member | Signature / notes |
|--------|-------------------|
| `AddItem` | `(Item:entity, ?AllowMergeItems:logic)<transacts>:result(add_item_result, []add_item_error)` — this inventory only |
| `AddItemDistribute` | same signature, also considers sub-inventories. **The default grant call.** |
| `RemoveItem` | `(Item:entity)<transacts>:result(remove_item_result, []remove_item_error)` |
| `GetItems()` | `[]entity`, this inventory only |
| `GetItems(Type:castable_subtype(item_component))` | filtered by item component type |
| `FindItems()` | `generator(entity)` across sub-inventories |
| `GetInventories()` / `FindInventories()` | `[]inventory_component` / `generator(...)` |
| `GetEquippedItems()` | `[]entity` |
| `AddItemEvent` / `RemoveItemEvent` / `EquipItemEvent` / `UnequipItemEvent` | `listenable(...)` |

`AddItem` / `AddItemDistribute` / `RemoveItem` are gated
`@available {MinUploadedAtFNVersion := 3800}`.

### `item_component` (same module)

`GetParentInventory[]`, `IsEquipped[]`, `Equip()`, `Unequip()`, `Drop[]`
(removes from inventory and places it in the world), `PickUp[Inventory]`,
`Categories:[]item_category`, `ChangeInventoryEvent`, `ChangeEquippedEvent`.

### Where the item and weapon classes live

| Module | Contents |
|--------|----------|
| `/Fortnite.com/Weapons` | ~300 weapon entity classes, e.g. `AssaultRifle_BR_CH4S1_Rare`, `BoltActionSniperRifle_BR_PreSeason_Epic` |
| `/Fortnite.com/Items` | consumables and world items, e.g. `WhiteMushroom_Creative_V1_Uncommon` |
| `/Fortnite.com/Armory` | creator-customisable templates, e.g. `assault_rifle_template` |
| `/Fortnite.com/Itemization/FortniteRarities` | `Common`, `Uncommon`, `Rare`, `Epic`, `Legendary`, `Mythic`, `Exotic` |
| `/Fortnite.com/Itemization/FortniteItemCategories` | category instances for `item_component.Categories` |

**Custom Armory weapons** (re-skin + tune AR/pistol/shotgun/SMG prefabs, not
stock `AssaultRifle_BR_*` classes) → load
`skill_read_subskill("scenegraph", "custom_weapons")`. **Custom non-weapon
Entity Prefab items** (mesh/icon/pickup, KFM spin, equipped detect) →
`skill_read_subskill("scenegraph", "custom_items")`. **Template abilities**
(Spicy Sprint, `fort_item_ability_component`, AbilityElements) →
`skill_read_subskill("scenegraph", "template_abilities")`. This file covers stock
`/Fortnite.com/Weapons` / `/Fortnite.com/Items` grants and shared
inventory/pickup APIs.

Each weapon is `class<final><concrete>(entity)`, so `{}` constructs one. Find
them without guessing:

```
list_verse_types({"kind": "class", "name_filter": "Shotgun"})
search_verse_digest({"query": "Pistol_BR"})
get_verse_api({"name": "AssaultRifle_BR_CH4S1_Rare"})
```

### Recipe A — trigger grants a configurable list

```verse
item_granter_component<public> := class<final_super>(component):

    @editable Trig : trigger_device = trigger_device{}
    @editable Items : []concrete_subtype(entity) = array{}   # pick item/weapon types in Details; concrete so {} can construct them

    TriggerAwait()<suspends>:void =
        loop:
            mAgent := Trig.TriggeredEvent.Await()
            if:
                Agent := mAgent?
                Inventory := (for (InvComp : Agent.FindDescendantComponents(inventory_component)) do InvComp)[0]
            then:
                for (Item : Items):
                    Inventory.AddItemDistribute(Item{})

    OnSimulate<override>()<suspends>:void =
        spawn{ TriggerAwait() }
```

The four things that break this if you change them:

1. `FindDescendantComponents` returns a **generator**, so
   `(for (X : Gen) do X)[0]` converts and indexes it — and indexing is failable,
   which is why the whole thing sits inside `if: … then:`.
2. `@editable` takes `[]subtype(entity)` (a list of *types*), but only a
   `concrete_subtype(entity)` can be instantiated — hence the local
   `ItemConcrete` before `{}`.
3. `AddItemDistribute` returns a `result`, it is **not** failable. Do not wrap
   it in `if`; read the result if you care whether the inventory was full.
4. One item entity belongs to exactly one inventory. Construct a **fresh**
   entity per grant instead of reusing one instance across players.

`spawn{ TriggerAwait() }` and `spawn. TriggerAwait()` are the same expression —
Verse allows a single-expression block after a dot. These packs use braces.

### Recipe B — grant one known weapon

```verse
GrantRifle(Agent:agent):void =
    if (Inventory := (for (I : Agent.FindDescendantComponents(inventory_component)) do I)[0]):
        Inventory.AddItemDistribute(AssaultRifle_BR_CH4S1_Rare{})
```

If your component already derives from `fort_item_pickup_interactable_component`
there is a cleaner lookup: `GetInteractorInventory(Agent)<transacts><decides>:inventory_component`.

**Custom Armory prefabs (`EP_*`) are not stock WIDs.** `AddItemDistribute` can
succeed while the gun is still unparented. Parent/equip is
`GetParentInventory[]` then `Equip()`, else `PickUp[Inventory]` then
`Equip()` — `skill_read_subskill("scenegraph", "custom_weapons")`. Owned
collectible + persist + shop: `skill_read_subskill("verse", "sys_owned_weapons")`.
`item_granter_device` cannot grant a custom Armory prefab.

### Recipe C — a pickup in the world

`fort_item_pickup_interactable_component` (`/Fortnite.com/Itemization`, gated
`MinUploadedAtFNVersion := 4040`) extends `basic_interactable_component`. Its
digest is explicit about the requirements: the owning entity needs an
`item_component` **and** a `mesh_component`, and the interacting agent needs a
subentity with an `inventory_component`.

```verse
if (Sim := Entity.GetSimulationEntity[]):
    Loot := AssaultRifle_BR_CH4S1_Rare{}    # already carries its item/mesh setup
    Sim.AddEntities(array{Loot})
    Loot.SetGlobalTransform(DropPose)
```

Prefer parenting a spawned item directly to the entity that should own it
rather than to the simulation root — deep-hierarchy transform reads are buggy
(see `movement_transforms`). For an item that is already held, `Drop[]` puts it
back into the world and `PickUp[Inventory]` is the inverse.

### Equipping and reacting

```verse
OnBeginSimulation<override>():void =
    (super:)OnBeginSimulation()
    set MaybeSub = option{ Inventory.AddItemEvent.Subscribe(OnItemAdded) }

OnEndSimulation<override>():void =
    (super:)OnEndSimulation()
    if (Sub := MaybeSub?) { Sub.Cancel() }
```

`item_component.Equip()` / `Unequip()` return `result(false, []equip_item_error)`
and fail when the item is not in an inventory or a query event vetoed it.
`inventory_component.GetEquippedItems()` reads the current loadout.

Stackables merge instead of occupying a new slot: `?AllowMergeItems := true` on
the add, plus `CanMergeInto[]` / `MergeInto[]` / `AllowMergeInto[]` /
`OnMergeInto` on the stackable component.

### Gotchas

- **Never `spawn_actor` an item or weapon class.** They are entity classes from
  the digests, not placeable Blueprint actors.
- **`trigger_device` is a device**, not an entity. It is an `@editable` on your
  component, picked in the Details panel — device wiring tools
  (`wire_verse_device_ref`) target Verse devices, not entity components.
- The component only appears under Add Component **after** a successful Verse
  build.
- Inventories need an itemization inventory configuration on Island Settings
  (`CustomInventoryConfiguration`, e.g. the BR-style asset — see
  `skill_read_subskill("islandsettings", "recipes")`). Without one, grants can
  succeed in Verse and show nothing on the HUD. Custom Armory grant parent/equip
  is `GetParentInventory` / `PickUp` / `Equip` (`custom_weapons` /
  `sys_owned_weapons`), not `case AddResult.Ok`.
- Subscribe to inventory events in `OnBeginSimulation` and cancel in
  `OnEndSimulation` (`verse_authoring`).
- Check the `MinUploadedAtFNVersion` gates above before relying on a call in a
  shipped island.
