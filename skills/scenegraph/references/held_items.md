---
description: "Held items (v42.30) — /Fortnite.com/Armory held_item_template: carryable non-weapon prefabs (torch by default → lantern, tool, banner, prop), Entity Prefab setup, reskin, Verse grant/equip, ADS toggles on weapons"
metadata:
  order: 8
  label: "Held items (v42.30)"
  default_enabled: false
  load_condition: "Something the player carries or holds that is not a weapon (torch, lantern, flashlight, tool, banner, sign, bucket, prop in hand), held_item_template, Custom Weapons: Held Items, or reskinning the torch"
---

# Held items (v42.30)

42.30 adds a fourth kind of Armory prefab: a **carryable item that is not a
weapon**. `held_item_template` (`/Fortnite.com/Armory`,
`@available {MinUploadedAtFNVersion := 4230}`) is a ready-to-customize Entity
Prefab — it ships with a **torch** mesh and icon. Reskin it into a lantern, a
tool, a banner, a flashlight, any prop the player equips and holds.

It sits next to the weapon templates (`pistol_template`, `assault_rifle_template`,
`shotgun_template`, `sub_machine_gun_template` — `custom_weapons`) and follows
the same workflow. Verified: `held_item_template{}` + `AddItemDistribute` +
`Equip()` compiles in 42.30 (Tycoony, Oct 1 2026).

## Pick the right path

| Goal | Use |
| --- | --- |
| Hold a prop / tool / light in hand | **this file** |
| A gun with fire/reload | `custom_weapons` |
| An item with your own behavior (no hold pose needed) | `custom_items` |
| Stock Fortnite items | `itemization` |

## Project gates

Same as custom weapons: **Project Settings → Custom Items in Inventory** = true,
and an island **itemization inventory configuration** (else the hotbar stays
empty — `islandsettings` `recipes`).

## Author the prefab

1. Content Drawer → right-click → **Entity Prefab** → switch **template** →
   **Held Item** (`held_item_template`). Name it (e.g. `Lantern`).
2. In the prefab editor swap the mesh (child mesh entity — keep pivot/axis fixes
   on the child, `movement_transforms`) and the icon on the item's description /
   icon components. Keep `item_component` and the pickup component.
3. Save. After a Verse build the prefab is a class in the Assets digest —
   `list_verse_types(digest="assets", name_filter="Lantern")` — use that name in Verse.

## Grant and equip from Verse

```verse
using { /Fortnite.com/Armory }
using { /Fortnite.com/Devices }
using { /UnrealEngine.com/Itemization }
using { /Verse.org/SceneGraph }
using { /Verse.org/Simulation }

# Inventory lives on a descendant of the agent.
GetHeldInventory(Agent:agent)<transacts><decides>:inventory_component =
    (for (Inv : Agent.FindDescendantComponents(inventory_component)) do Inv)[0]

held_item_granter_device := class(creative_device):
    @editable GrantButton : button_device = button_device{}

    OnBegin<override>()<suspends>:void =
        GrantButton.InteractedWithEvent.Subscribe(OnGrant)

    OnGrant(Agent:agent):void =
        if (Inventory := GetHeldInventory[Agent]):
            # Your prefab from the Held Item template (Assets.digest name), e.g. Lantern{}.
            Item := held_item_template{}
            if (IC := Item.GetComponent[item_component]):
                Inventory.AddItemDistribute(Item)
                if (IC.GetParentInventory[]):
                    IC.Equip()
                else if (IC.PickUp[Inventory]):
                    IC.Equip()
                else:
                    Item.RemoveFromParent()
            else:
                Item.RemoveFromParent()
```

Do not `case` the `AddItemDistribute` result to decide Equip — check
`GetParentInventory[]`, else `PickUp[Inventory]`, else clean up (same as
`custom_weapons`). On join, poll until the inventory exists (`custom_weapons`).

## Also new in 42.30 (weapons)

`fort_trace_weapon_component` gained two editable toggles with setters:
`AllowAimDownSightsInAir` / `SetAllowAimDownSightsInAir(Val:logic)` and
`AllowAimDownSightsDuringReload` / `SetAllowAimDownSightsDuringReload(Val:logic)`.

42.30 fixes that matter here: equipping an item from Verse no longer leaves the
player unable to aim or shoot, and `RemoveItemEvent`'s `RemovedAmount` is no
longer always 0.
