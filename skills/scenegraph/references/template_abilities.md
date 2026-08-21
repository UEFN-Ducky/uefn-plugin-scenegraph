---
description: "Fortnite template abilities — Scene Graph item prefabs with fort_item_ability_component, fort_template_ability Verse class, status-effect AbilityElements (burn/pepper), input triggers (IA_Sprint), and hotbar grant"
metadata:
  order: 9
  label: "Template abilities"
  default_enabled: false
  load_condition: "Building a Fortnite template ability, Spicy Sprint, fort_template_ability, fort_item_ability_component, AbilityElements, status-effect burn/pepper, IA_Sprint, self_ability_target_query, granting an ability item to the weapon hotbar, or an item that fires an ability on input"
---

# Fortnite template abilities (Scene Graph)

Template abilities are **custom item Entity Prefabs** that run Epic’s ability
stack (`fort_template_ability` + `fort_item_ability_component`) instead of a
hand-rolled Verse `OnBeginSimulation` loop. First recipe: **Spicy Sprint** —
Sprint input applies burn DoT + pepper speed at once.

Not Armory firearms (`custom_weapons`). Not a Creative Item Granter. Not a
custom item whose “ability” is only a Verse component (`custom_items`).

## Digest gate (do this first)

This API is experimental. **Never guess.** On the current island:

```
search_verse_digest({"query": "fort_template_ability"})
get_verse_api({"name": "fort_template_ability"})
get_verse_api({"name": "fort_item_ability_component"})
get_verse_api({"name": "fort_ability_status_effect_burn_point"})
get_verse_api({"name": "fort_ability_status_effect_pepper_point"})
```

Empty digest → Project Settings: enable **Scene Graph Experimental Features**
and **Custom Items and Inventory**, then Verse build. Still empty → UEFN too
old; stop. Do not invent types.

Confirm every member you set in Details (`ItemAbilities`, `InputTrigger`,
`TargetQuery`, `AbilityElements`, `StatusEffectDuration`, `Time`) with
`get_verse_api` on this build.

## Project gates

1. **Project Settings → Scene Graph Experimental Features**
2. **Project Settings → Custom Items and Inventory**
3. Island inventory HUD configured (`islandsettings` recipes) or the granted
   item never shows

## Choose the path

| Goal | Load |
|------|------|
| **Template ability item (Sprint / status effects / AbilityElements)** | **this file** |
| Custom item with your own Verse-while-held logic | `custom_items` |
| Custom Armory gun | `custom_weapons` |
| Stock Fortnite gun grant | `itemization` |

## Mental model

```
Verse (compile first)
└── template_ability := class(fort_template_ability(...))
    └── MakeContext / MakeAbility / ActiveEffects
        → exposes inherited properties on the item prefab

Entity Prefab (ability item)
├── item_component                    Categories: WeaponMelee (Spicy Sprint)
└── fort_item_ability_component
    ├── ItemAbilities[0]              always-on, or ItemEquippedAbilities if held-only
    │   ├── type = your template_ability class
    │   ├── InputTrigger = IA_Sprint (Assets_input_action)
    │   ├── TargetQuery = self_ability_target_query
    │   └── AbilityElements[]
    │       ├── fort_ability_status_effect_burn_point    (DoT)
    │       └── fort_ability_status_effect_pepper_point  (speed)
    └── optional StatusEffectDuration / Time per element

Level
├── PF_* item prefab INSTANCE         (drag / instantiate_prefab)
└── template_ability_item_granter_device
    └── @editable TemplateAbilityItemEntity → that INSTANCE (not the asset)
```

**Do not** put `fort_inventory_weapon_hotbar_component` on the **item**. That
type lives on the **player**. Grant queries it from the player.

## Agent workflow

1. `workspace_write_file("Verse/Abilities/template_ability_example.verse", …)`
   — never dump at `Content/Verse/` root.
2. `workspace_list_verse_errors`. Clean + UEFN open → `workspace_compile_verse`.
3. `create_empty_prefab` (`PF_SpicySprintItem` under project Prefabs). MCP
   cannot see EntityPrefab tabs — add comps in UEFN Prefab Editor, **Save**.
4. `instantiate_prefab` the item into the level + `save_current_level`.
5. Place the compiled Verse granter device (Content Browser after Verse build).
   Details → `TemplateAbilityItemEntity` = the **placed instance**.
6. Launch Session. Sprint → burn + speed.

Prefab-owned edits: Save the EntityPrefab (`prefab_only`). Serial MCP: one
heavy call per turn.

## Prefab Details (Spicy Sprint)

Content Browser → Entity Prefab → `PF_SpicySprintItem` → Prefab Editor:

1. Add `item_component`. Categories → add `FortniteItemCategories.WeaponMelee`.
2. Add `fort_item_ability_component`.
3. **ItemAbilities** (always available) — or **ItemEquippedAbilities** if the
   ability should fire only while the item is equipped.
4. Index[0] type = `template_ability` (your compiled class). Expand it:
   - **InputTrigger** → `Assets_input_action` → `IA_Sprint`
   - **TargetQuery** → `self_ability_target_query`
   - **AbilityElements** two entries:
     - `[0]` `fort_ability_status_effect_burn_point` (periodic health damage)
     - `[1]` `fort_ability_status_effect_pepper_point` (movement speed)
   - Optional: `StatusEffectDuration` and `Time` per element (layer effects
     at different `Time` for sequences).
5. Save the prefab. Drag / `instantiate_prefab` into the level.

Other `TargetQuery` options exist (reticle / AoE) — `get_verse_api` /
`search_verse_digest("ability_target_query")` before picking one.

## Verse — complete Spicy Sprint + granter

Path: `Verse/Abilities/template_ability_example.verse`

```verse
using { /Fortnite.com/Abilities }
using { /Fortnite.com/Devices }
using { /Fortnite.com/Itemization }
using { /UnrealEngine.com/Abilities }
using { /UnrealEngine.com/Itemization }
using { /Verse.org/SceneGraph }
using { /Verse.org/Simulation }

# First fort_inventory_weapon_hotbar_component on the PLAYER (not the item).
(Player : player).GetWeaponHotbarComponent()<decides><transacts> : fort_inventory_weapon_hotbar_component =
    first (WeaponHotbarComponent : Player.FindDescendantComponents(fort_inventory_weapon_hotbar_component)) {WeaponHotbarComponent}

# Defining this type exposes inherited properties on the item prefab.
template_ability := class(fort_template_ability(ability_context, fort_template_ability_effect)):

    var ActiveEffects<override> : []fort_template_ability_effect = array{}

    MakeContext<override>()<transacts> : ability_context =
        ability_context{}

    MakeAbility<override>()<transacts> : fort_template_ability_effect =
        fort_template_ability_effect{}

template_ability_item_granter_device := class(creative_device):

    @editable
    TemplateAbilityItemEntity : entity = entity{}

    GrantItemTo(Player : player) : void =
        if:
            WeaponHotbarComponent := Player.GetWeaponHotbarComponent[]
            ItemComponent := TemplateAbilityItemEntity.GetComponent[item_component]
        then:
            WeaponHotbarComponent.AddItem(TemplateAbilityItemEntity)
            ItemComponent.Equip()

    OnBegin<override>()<suspends> : void =
        if (FirstPlayer := GetPlayspace().GetPlayers()[0]):
            GrantItemTo(FirstPlayer)
```

Signatures above are Epic’s published quickstart. If `workspace_list_verse_errors`
disagrees, **digest wins** — `get_verse_api` and fix. Do not patch `*.digest.verse`.

## Playtest

Launch Session. Sprint → health ticks from burn, move speed up from pepper.

## Extend

- Other `TargetQuery` (reticle / area).
- Other `AbilityElements` (digest-search `fort_ability_status_effect_`).
- Stagger `Time` on elements for sequences.
- Held-only: `ItemEquippedAbilities` instead of `ItemAbilities`.
