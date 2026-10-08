# 3D engine evaluation — 2026-10-08

Captured verbatim from the design-phase agent response below. This is a working recommendation for the controller to act on next, not an owner-approved architecture decision or a claim that the chosen approach has been benchmarked on real hardware.

---

Good, this confirms the decision record's description matches actual code. I have enough to produce the recommendation now.

## Recommendation

**Keep `com.google.android.filament:filament-android` as the engine; add `com.google.android.filament:filamat-android` as the second, same-family dependency required to compile a renderable material in-process.**

This matches and confirms what `docs/decisions/3D_ENGINE_EVALUATION.md` already recorded for this exact question, cross-checked against the current `app/build.gradle.kts`/`gradle/libs.versions.toml` and `EngineHarness.kt` (which still renders only a Filament `Skybox` plus a Compose-`Canvas` cube — the flat/no-geometry gap the task flags).

**Coordinates:**
- `com.google.android.filament:filament-android:1.56.0` — unchanged, already verified against Maven Central's `maven-metadata.xml` (1.56.5 doesn't resolve, 1.56.0 does; POM/AAR both HTTP 200). Already pinned in the version catalog; no action needed.
- `com.google.android.filament:filamat-android` — **version not verified, do not guess.** Filament artifacts release in lockstep so `1.56.0` is plausible, but that must be confirmed against Maven Central's `maven-metadata.xml` (and a resolving POM/AAR) before it goes in `libs.versions.toml`. This is exactly the kind of guess the task warns against repeating.

**Why a second dependency is needed at all:** `RenderableManager` needs a `Material` built from compiled `.filamat` bytes. The only documented way to produce those is the `matc` CLI (no shell/build-tool access in this phase or the prior implementing session) or `filamat-android`'s `MaterialBuilder` API — the same compiler, exposed as a library. It needs no Gradle plugin, no NDK/CMake, and no `settings.gradle.kts` change, so it stays within the task's one-extra-dependency carve-out.

**Main trade-off:** `filamat-android` ships a full native shader cross-compiler (glslang/spirv-cross/spirv-opt) per ABI — heavier than a precompiled `.filamat` blob, plus a one-time runtime-compile cost at first launch. The better long-term shape is compiling the material once in a dev-time/CI step and shipping only the small compiled asset, dropping `filamat-android` from the release graph — but that needs a scoped follow-up with shell/build access, not something to solve in this file-tools-only phase.

**Other criteria:** unchanged from the existing record — accessibility/automation keep working because `EngineHarness.kt`'s Filament `AndroidView` stays `clearAndSetSemantics {}` with the real `testTag("engine-canvas")` on the Compose `Box`, so `agent/visual_qa.py`'s existing tap-by-tag flow needs no new mechanism; asset licensing is unaffected since the mesh is a hand-built procedural cube and the material is authored in-process, not imported; performance/thermal cost on real hardware remains unverified and should stay flagged as an open risk.

**Confidence:** this is a working recommendation for the next bounded milestone, not a verified result — `filamat-android`'s exact version and a real `MaterialBuilder` run against this Filament build still need to be checked before implementation.
