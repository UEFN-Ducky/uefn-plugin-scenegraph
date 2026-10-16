---
description: "Custom abilities in Verse (/UnrealEngine.com/Abilities, out of Experimental in 42.40) — ability(context, effect), ability_context (Instigator is ?entity since 42.40), ability_effect prefab + ability_effect_component lifecycle (OnBeginUse, OnSimulate, OnEndUse, EndUse, Cancel / CanCancel, cancel_reason), Use() is no_rollback, BeginUseEvent / EndUseEvent, granting to players with input, a compiled heal-over-time example"
metadata:
  order: 10
  label: "Custom abilities (Verse, v42.40)"
  default_enabled: false
  load_condition: "Writing a gameplay ability in Verse — spells, powers, heal over time, channelled or cancellable effects, ability(…) / ability_context / ability_effect / ability_effect_component, Use() / CanUse / Cancel, cooldowns or stacking rules, or reading who used an ability (Instigator)"
---

# Custom abilities (Verse)

Two ways to make an ability:

| Want | Use |
| --- | --- |
| Input → timeline of effects (animation, VFX, sound, damage, heal, status effects, attribute modifiers, projectiles) with no Verse logic | **Template abilities** — `template_abilities` |
| Your own rules: channelling, stacking limits, custom targets, cancel on jump, per-tick logic | **This page** — subclass `ability(context, effect)` |

**42.40:** the ability types lost `@experimental` (no 2304 warning when they compile),
so islands that use them can publish. Epic's "Create Your First Ability" page still
says to enable **Scene Graph Experimental Features**; if `get_verse_api({"name":
"ability"})` finds nothing on the island, enable it and build Verse.

## The four parts (42.40 digest)

```verse
using { /UnrealEngine.com/Abilities }
```

| Part | Declaration | Role |
| --- | --- | --- |
| Ability | `ability(context_type, ability_effect_type) := class<abstract>(has_icon)` | Persistent definition. `Use(Parent:entity, Context:context_type):?ability_effect_type` (final), `CanUse(...)<decides><reads>`, `MakeContext()<transacts>`, `MakeAbility()<transacts>`, `ActiveEffects`, `BeginUseEvent` / `EndUseEvent : listenable(entity)`, `Icon` |
| Context | `ability_context := class<concrete>` | Per activation: `var Instigator : ?entity`, `var Participants : []entity`, `var Targets : []entity`. Subclass to carry your own data |
| Effect | `ability_effect := class<concrete>(entity)` | The spawned entity, usually a prefab made from **ability_effect** in Create Entity Prefab Definition |
| Effect component | `ability_effect_component := class<final_super>(component)` | Logic + lifetime: `OnBeginUse()<transacts>`, `OnSimulate()<suspends>`, `OnEndUse(Reason:?cancel_reason)<transacts>`, `EndUse(?cancel_reason)` (protected), `Cancel[Reason]` (public, `<decides>`), `CanCancel(Reason)<transacts><decides>`, `Context : ?ability_context`, `Ability` |

Cancel reasons: subclass `cancel_reason` (`<castable>`) — `jump_cancel :=
class(cancel_reason){}`; built-ins `ability_ended`, `ability_removed_from_scene`.

## Lifecycle (Epic)

1. Your manager builds a context and calls `Ability.Use(Parent, Context)`.
2. `Use` runs `CanUse` (stop here if it fails) → `MakeContext` (the effect keeps a
   copy) → `MakeAbility` (the effect entity) → adds it to `ActiveEffects` → returns it.
3. The effect component's `OnBeginUse` runs, then `BeginUseEvent` fires.
4. `OnSimulate` runs until `EndUse` or an accepted `Cancel` (`CanCancel` decides).
5. `OnEndUse` runs, `EndUseEvent` fires, the effect leaves `ActiveEffects` and is destroyed.

Lifetimes: ability = persistent; context = per activation (copy lives with the effect);
effect and component = until the effect ends.

## 42.40 changes

- `ability_context.Instigator` is `?entity` (was `?agent`). Assigning an agent still
  works (`agent` is a subclass of `entity`): `Instigator := option{PlayerAgent}`.
  Reading needs a cast: `agent[Context.Instigator?]` — using it as an agent directly is
  Script error 3509.
- `fort_projectile_component.GetInstigator[]` returns an `entity` too.
- `MakeAbilityEffectComponent` is gone.
- A failed `Use` now logs why. Fixed: `Use()` with a player instigator, rejected uses
  running their timeline, `Cancel` not stopping a timeline, end events firing twice or
  not at all after unequipping mid-use; target queries return entities for players and NPCs.

## Rules that decide whether it compiles

- **`Use` is `no_rollback`.** Never call it inside `if (…)`, a `for` filter or a
  `<decides>` function (Script error 3512). Call it on its own line, then unwrap:
  `Spawned := Ability.Use(Parent, Ctx)` → `if (Effect := Spawned?):`.
- Overrides keep the digest effects exactly: `CanUse<override>(Parent:entity,
  Ctx:my_context)<reads><decides>:void`, `MakeContext<override>()<transacts>`,
  `OnBeginUse<override>()<transacts>`, `OnSimulate<override>()<suspends>`,
  `OnEndUse<override>(Reason:?cancel_reason)<transacts>`.
- Override `var ActiveEffects<override> : []ability_effect = array{}`.
- `MakeAbility` returns your effect prefab: `Prefab := PF_HealEffect{}` then
  `if (E := ability_effect[Prefab]): return E`, else `return ability_effect{}`. In the
  prefab, delete the stock `ability_effect_component` and add yours (Prefab Editor →
  Save; MCP can't see prefab tabs — `prefab_only`).

## Example — heal over time, cancelled by a jump

Compiled with 0 errors / 0 warnings in UEFN 42.40 (Epic's tutorial ability with
`MakeAbility` returning a bare `ability_effect{}` — swap in your prefab).

```verse
using { /Fortnite.com/Characters }
using { /Fortnite.com/Input }
using { /Fortnite.com/Playspaces }
using { /UnrealEngine.com/Abilities }
using { /Verse.org/Input }
using { /Verse.org/SceneGraph }
using { /Verse.org/Simulation }

(TargetEntity:entity).HealFortChar()<decides><transacts>:fort_character =
    (for (Component : TargetEntity.GetComponents(), FortChar := fort_character[Component]) do FortChar)[0]

# Instigator is an entity: walk up until one of them is an agent.
(Entity:entity).OwningAgent()<decides><transacts>:agent =
    if (Agent := agent[Entity]):
        Agent
    else:
        Entity.GetParent[].OwningAgent[]

jump_cancel := class(cancel_reason){}

heal_context := class(ability_context):
    HealPerTickOverride : ?float = false

heal_effect_component := class(ability_effect_component):
    @editable
    var HealPerTick : float = 5.0
    @editable
    var TickInterval : float = 2.0
    @editable
    var MaxDuration : float = 10.0

    OnJumped(FortCharacter : fort_character) : void =
        if (Cancel[jump_cancel{}]):
            return

    OnBeginUse<override>()<transacts> : void =
        if (HealContext := heal_context[Context?]):
            if (Override := float[HealContext.HealPerTickOverride?]):
                set HealPerTick = Override

    OnSimulate<override>()<suspends> : void =
        var Elapsed : float = 0.0
        if:
            InstigatorEntity := Context?.Instigator
            InstigatorAgent := InstigatorEntity?.OwningAgent[]
            FortChar := InstigatorAgent.GetFortCharacter[]
        then:
            FortChar.JumpedEvent().Subscribe(OnJumped)
        loop:
            Sleep(TickInterval)
            set Elapsed += TickInterval
            if (AbilityContext := Context?):
                for (Target : AbilityContext.Targets, TargetChar := Target.HealFortChar[]):
                    TargetChar.Heal(HealPerTick)
            if (Elapsed >= MaxDuration):
                EndUse(false)
                break

    OnEndUse<override>(Reason:?cancel_reason)<transacts>:void =
        if (jump_cancel[Reason?]):
            Print("heal cancelled by a jump")

heal_ability := class(ability(heal_context, ability_effect)):
    var ActiveEffects<override> : []ability_effect = array{}

    # One heal at a time.
    CanUse<override>(AbilityEffectParent : entity, AbilityContext : heal_context)<reads><decides> : void =
        (ActiveEffects.Length = 0)

    MakeContext<override>()<transacts> : heal_context = heal_context{}

    MakeAbility<override>()<transacts> : ability_effect = ability_effect{}

# Lives on each player's character entity; secondary fire uses the ability.
heal_manager_component := class<final_super>(component):
    HealAbility : heal_ability = heal_ability{}
    OwningPlayer : player

    OnSecondaryFire(Args : tuple(player, logic)) : void =
        if:
            Args(1)?
            PlayerAgent := agent[Args(0)]
            PlayerEntity := PlayerAgent.GetFortCharacter[].GetEntity[]
        then:
            HealContext := heal_context:
                Instigator := option{PlayerAgent}
                Participants := array{}
                Targets := array{PlayerEntity}
                HealPerTickOverride := option{10.0}
            Spawned := HealAbility.Use(PlayerEntity, HealContext)   # never inside an if
            if (Effect := Spawned?):
                HealAbility.EndUseEvent.Subscribe(OnEffectEnded)

    OnSimulate<override>()<suspends> : void =
        if (PlayerInput := GetPlayerInput[OwningPlayer]):
            PlayerInput.AddInputMapping(Character.RangedWeaponMapping)
            PlayerInput.GetInputEvents(Character.WeaponSecondary).TriggerActivationEvent.Subscribe(OnSecondaryFire)

    OnEffectEnded(EffectEntity : entity) : void =
        EffectEntity.RemoveFromParent()
```

Give every player the manager (Epic's pattern): a watcher component on a level prefab
that, for each player (and on `PlayerAddedEvent()`), makes an empty `entity{}`, adds
`heal_manager_component{Entity := FortCharEntity, OwningPlayer := Player}` with
`AddComponents`, and attaches it with `FortCharEntity.AddEntities(array{Manager})`.

## Using a template ability from Verse

`fort_template_ability` is an `ability(ability_context, fort_template_ability_effect)`,
so the same call works — and works with a player instigator since 42.40:

```verse
TryUse(Ability:fort_template_ability, Agent:agent):logic =
    if (Character := Agent.GetFortCharacter[], CharEntity := Character.GetEntity[]):
        Ctx := ability_context{Instigator := option{Agent}, Participants := array{}, Targets := array{CharEntity}}
        Spawned := Ability.Use(CharEntity, Ctx)
        if (Spawned?):
            return true
    return false
```
