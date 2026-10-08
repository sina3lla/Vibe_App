# 3D engine evaluation — 2026-10-08

Captured verbatim from the design-phase agent response below. This is a working recommendation for the controller to act on next, not an owner-approved architecture decision or a claim that the chosen approach has been benchmarked on real hardware.

---

## Recommendation: keep Filament, add `filamat-android` as the second, same-family dependency needed to render real geometry

**Core dependency (unchanged, already verified — use as-is):**
```
com.google.android.filament:filament-android:1.56.0
```
This version is already pinned in `gradle/libs.versions.toml` and verified against Maven Central's `maven-metadata.xml` in `docs/decisions/3D_ENGINE_EVALUATION.md` (resolvable POM/AAR, API-compatible with the existing `EngineHarness.kt`). No change needed here; cite that record rather than re-deriving it.

**Second dependency — why it's needed:** the current `EngineHarness.kt` only gets a real Filament render for a `Skybox` (flat color). The actual visible shape (the rotating cube) is drawn with plain Compose `Canvas` 2D math layered on top, because `RenderableManager` requires a `Material` built from compiled `.filamat` bytes, and the only documented way to produce those is the standalone `matc` binary — a tool this file-tools-only phase (and the implementing session before it) has no shell access to run. That's exactly the "flat-colored background... not an acceptable final state" gap the task calls out.

`com.google.android.filament:filamat-android` is Filament's own runtime material compiler (the `MaterialBuilder` API) — the same compiler `matc` wraps, exposed as a library instead of a CLI binary. It lets the app compile a small hand-authored unlit/lit material definition in-process at startup, with no external binary, no Gradle plugin, no NDK/CMake, and no `settings.gradle.kts` change. That satisfies the task's carve-out for a second dependency "from the same engine family... specifically to display geometry."

**Version for `filamat-android`: not verified.** `docs/decisions/3D_ENGINE_EVALUATION.md` only checked `filament-android`'s Maven metadata; it says nothing about `filamat-android`. Filament's artifacts are normally released in lockstep, so `1.56.0` is a reasonable guess — but per the task's own instruction I will not supply that from memory. The exact `filamat-android` version must be checked against Maven Central's `maven-metadata.xml` (and that its POM/AAR actually resolve) before anyone adds it to `libs.versions.toml`.

**Main trade-off accepted:** `filamat-android` bundles a full shader cross-compiler (glslang/spirv-cross/spirv-opt) as native code, which is meaningfully heavier per-ABI than shipping a tiny precompiled `.filamat` blob, plus a one-time runtime compile cost at first launch (not per-frame). The better long-term shape is to run `matc` or `MaterialBuilder` once in a dev-time/CI step outside the shipped app, commit the small compiled asset, and drop `filamat-android` entirely from the release dependency graph — but that needs shell/build tool access this design phase and the prior implementing session didn't have. I'd flag that as a concrete, scoped follow-up ask rather than solve it now.

**Other criteria, briefly:**
- **Accessibility/verification:** no change to the existing pattern in `EngineHarness.kt` — the Filament `AndroidView` stays `clearAndSetSemantics {}`, the real `testTag("engine-canvas")`/`contentDescription` stay on the Compose `Box`, and `agent/visual_qa.py` only ever taps/screenshots via that tag, so swapping the cube's backing renderer doesn't require any new verification mechanism.
- **Asset licensing:** no change — the mesh stays a procedural, hand-built cube; the material is a hand-authored definition compiled in-process, not an imported third-party asset.
- **Performance:** unresolved risk carried over from the prior record — on-demand rendering (not free-running 60fps) is the intended approach, but frame-time/thermal cost is still unverified on real hardware.

**Confidence:** this is a working recommendation for the next bounded milestone, not a verified result — I haven't confirmed `filamat-android`'s Maven coordinates/version or run `MaterialBuilder` against this exact Filament build. Both need to be checked before implementation.

---

## Controller-verified AndroidX Test / Espresso fix (preparation session, 2026-10-08)

Out of scope note: this section only covers the Android test-infrastructure blocker below. It does not verify `filamat-android` (the open item directly above, from the current design recommendation) — that remains unresolved and is not part of what was asked this round.

**What happened:** `agent/runs/20261008-230038/engine-3-gradle.log` shows `connectedDebugAndroidTest` failing with the same error in three tests (`NavigationStateRestorationTest.destinationSurvivesActivityRecreation`, `EngineHarnessTest.firstCompositionDoesNotCrashAndExposesEngineCanvas`, `EngineHarnessTest.nonSpatialFallbackIsReachableWithoutTheRenderedSurface` — see `app/build/outputs/androidTest-results/connected/debug/TEST-Pixel_10(AVD) - 17.xml`):

```
java.lang.NoSuchMethodException: android.hardware.input.InputManager.getInstance []
	at androidx.test.espresso.base.InputManagerEventInjectionStrategy.initialize(InputManagerEventInjectionStrategy.java:28)
```

The emulator (`Pixel_10(AVD) - 17`) runs a platform build where the historically-hidden static method `InputManager.getInstance()` — which Espresso's event-injection layer locates via reflection — no longer exists with that signature. This is a known, already-fixed AndroidX Test compatibility gap, not an app bug and not something any test assertion should be weakened to work around.

**Verification performed** (direct Maven/official release-notes checks, not memory):
1. `https://dl.google.com/android/maven2/androidx/test/espresso/group-index.xml` (HTTP 200): latest stable `espresso-core` is `3.7.0` (this project was pinned to `3.5.1`).
2. `https://dl.google.com/android/maven2/androidx/test/ext/group-index.xml` (HTTP 200): latest stable `androidx.test.ext:junit` is `1.3.0` (this project was pinned to `1.1.5`).
3. Official release notes (`https://developer.android.com/jetpack/androidx/releases/test`), Espresso 3.7.0 (2025-07-30), Bug Fixes: **"Use getSystemService instead of reflective InputManager.getInstance"** — the exact defect being hit. (3.7.0's one API change is `minSdkVersion` → 21; this project's `minSdk = 24`, so no conflict. 3.6.0 similarly only raised its floor to API 19/then 21 and removed internal Guava usage — nothing used by this project's test code.)
4. Confirmed both artifacts actually resolve: `espresso-core-3.7.0.pom` and `junit-1.3.0.pom` both return HTTP 200 from `dl.google.com/android/maven2`.
5. `androidx.test:core`/`runner`/`rules`/`monitor` are **not** pinned explicitly in this project's version catalog — they come transitively from `espresso-core`/`androidx.test.ext:junit`'s own declared dependencies, so bumping only those two existing catalog entries is the smallest change; Google publishes the whole AndroidX Test family as a coordinated release train, so 3.7.0/1.3.0 should pull a mutually-compatible `core`/`runner`/`monitor` set automatically (latest stable there: `core` 1.7.0, `runner` 1.7.0, `rules` 1.7.0, `monitor` 1.8.0 — not pinned here, just confirmed to exist in case a future conflict needs an explicit override).

**Decision:** bumped `gradle/libs.versions.toml`'s `espressoCore` to `"3.7.0"` and `junitVersion` to `"1.3.0"` — both exact, verified-resolvable pins, no dynamic versions. No test assertions, skips, or app SDK targets were changed.

**Status:** awaiting the orchestrator's next `connectedDebugAndroidTest` run against the real emulator to confirm this actually fixes the three failures end to end (a successful Maven resolution and a documented fix are strong evidence, not proof of this specific run). If it does not, the next step is the full new `engine-N-gradle.log`/test-result XML, not another guessed dependency change.
