# Bertie S1 Progression (`bertie_s1`)

Stage-1 progression content for the **bertie** modpack. NeoForge **1.21.1** / Java **21**.

This is the content mod that implements the canonical S1 design — the gated crafting
progression, the custom items that open each gate, the Hephaestus Forge shaping rules,
and the recipe ledger that redirects the pack's early game through them.

> **Scope.** This mod is written for the bertie modpack. It assumes the pack's mod list is
> present and is not intended as a standalone drop-in. It targets no other Minecraft version.

---

## What it adds

### Items

| Item | Role |
|---|---|
| `crafting_license` | the gate token — carrying it is what unlocks gated recipes |
| `descent_anchor` | descent gating |
| `weeping_eye` | locator for the weeping structures |
| `finder` / `locator` | structure-finding items |

Plus the S1 material chain — dragonbone frames and braces, ignitium struts and lattices,
kinetic vanes and pattern plates, seals, resonances and attunements — each with its own
texture under `assets/bertie_s1/textures/item/`.

### Blocks

`echo_lock` and the victory ledger, registered through `ModBlocks`.

### Systems

- **Crafting gate** (`gate/CraftingGateHandler`) — recipes are withheld until the player
  holds the corresponding licence.
- **Catalyst recipes** (`recipe/CatalystShapedRecipe`) — a shaped recipe that requires a
  catalyst item present but does not consume it.
- **Hephaestus Forge integration** (`forge/`) — bed recipes, forge bed handling and
  pedestal formation rules layered onto Forbidden & Arcanus.
- **Deep Waters shrine** (`shrine/`) — the shrine handler plus a Ponder scene describing it.
- **Allay corruption** (`AllayCorruptionHandler`).
- **Removed items** (`RemovedItems`) — items withdrawn from the pack's progression.

### Data

Roughly 1,500 JSON files: the R01–R42 recipe ledger, ~250 darkstone stonecutting recipes,
31 Hephaestus Forge rituals, and recipe additions or overrides in the namespaces of the
pack's other mods (Create kinetics, Malum spirit infusion, Ice and Fire, Immersive Armors,
Twilight Forest equipment, Avaritia, Cataclysm, Deeper Darker, L2 Hostility loot modifiers
and others). A Patchouli field guide documents the progression in game.

---

## Building

```bash
./gradlew build
```

Requires **JDK 21**. The jar lands in `build/libs/`.

Toolchain is the shared bertie harness: NeoForge `21.1.217`, ModDevGradle `2.0.134`,
Gradle `8.8`. A `server()` run is wired for headless boot tests.

## Releasing

Bump `mod_version` in `gradle.properties`, then tag:

```bash
git tag v0.21.0 && git push origin v0.21.0
```

`release.yml` builds the jar and attaches it to a GitHub Release.

---

## Licence

Released into the public domain under **The Unlicense** — see [UNLICENSE](UNLICENSE).

This covers the original code and assets here. It does not cover the mods this one
depends on or interoperates with; those keep their own licences and none of their
content is redistributed in this repository.
