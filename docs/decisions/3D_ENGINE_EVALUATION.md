# 3D engine evaluation — 2026-10-08

Captured verbatim from the design-phase agent response below. This is a working recommendation for the controller to act on next, not an owner-approved architecture decision or a claim that the chosen approach has been benchmarked on real hardware.

---

## Recommendation

**Keep `com.google.android.filament:filament-android` as the 3D engine for this project; add `com.google.android.filament:filamat-android` as the one additional, same-family dependency needed to compile a real `Material` so `RenderableManager` can draw actual geometry instead of a skybox-only scene.**

This confirms what `docs/decisions/3D_ENGINE_EVALUATION.md` already recorded, and I checked it directly against current code rather than taking the record on faith: `app/build.gradle.kts`/`gradle/libs.versions.toml` already carry `filament-android` as the sole engine dependency, and `EngineHarness.kt` currently renders a Filament `Skybox` (background-only, no mesh) plus a hand-drawn Compose `Canvas` cube as the actual visible object — exactly the flat/no-geometry gap the task says is unacceptable as a final state.

**Coordinates:**
- `com.google.android.filament:filament-android:1.56.0` — already pinned, and the version catalog's own comment documents it was verified against Maven Central's `maven-metadata.xml` (1.56.5 doesn't resolve; 1.56.0's POM/AAR both return HTTP 200). No change needed.
- `com.google.android.filament:filamat-android` — **version not verified; do not guess.** It is plausible it ships lockstep with `1.56.0` since Filament releases its artifacts together, but that must be independently confirmed against Maven Central's `maven-metadata.xml` with a resolving POM/AAR before anyone adds it to `libs.versions.toml`. A prior cycle's guessed patch version for a different artifact (`1.56.5`) did not exist — the same mistake must not be repeated here from memory.

**Why a second dependency, and why this one:** Filament's `RenderableManager` requires compiled `.filamat` bytes for any renderable mesh. The only ways to produce them are the `matc` CLI (unavailable — no shell/build-tool access in this phase, and no NDK/CMake or Gradle-plugin path is permitted by the task) or `filamat-android`'s in-process `MaterialBuilder` API, which is the same compiler shipped as a library from the same engine family. It needs no Gradle plugin, no native build system, and no `settings.gradle.kts` change, so it fits the task's one-extra-dependency carve-out cleanly.

**Against the evaluation criteria:**
- **Accessibility/automation:** unaffected either way — `EngineHarness.kt` already keeps the Filament `AndroidView` `clearAndSetSemantics {}` and puts the real `testTag("engine-canvas")`, description, and tap action on the surrounding Compose `Box`. `agent/visual_qa.py`'s existing tap-by-resource-id flow needs no new mechanism, now or after `filamat-android` lands.
- **Asset licensing:** no third-party models involved; the mesh is procedural (hand-authored cube) and the material would be authored in-process via `MaterialBuilder`, not imported, so there's nothing to flag.
- **Integration cost:** stays within the ceiling — one engine, one small same-family compiler, no plugin/NDK/toolchain/settings change.
- **Performance:** unmeasured on real hardware either way. `filamat-android` additionally bundles a native shader cross-compiler (glslang/spirv-cross/spirv-opt) per ABI, which is heavier than shipping a precompiled `.filamat` blob and adds a one-time compile cost at first use. The better long-term shape is compiling the material once in a dev-time/CI step and shipping only the compiled asset, dropping `filamat-android` from the release dependency graph — but that needs shell/build access this phase doesn't have, so it's a follow-up, not something to resolve now.

**Main trade-off accepted:** paying `filamat-android`'s native-compiler weight and first-run compile cost now, in exchange for not needing any new build infrastructure, in order to get a genuinely renderable Filament object rather than a permanent skybox-plus-Canvas-cube substitute.

**Confidence:** this is a working recommendation for the next bounded milestone, not a benchmarked or owner-approved result — `filamat-android`'s exact version still needs Maven-metadata verification, and no frame-time/thermal/battery measurement exists on real hardware yet.
