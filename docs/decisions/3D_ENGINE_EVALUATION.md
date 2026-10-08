# 3D engine evaluation — 2026-10-08

Captured verbatim from the design-phase agent response below. This is a working recommendation for the controller to act on next, not an owner-approved architecture decision or a claim that the chosen approach has been benchmarked on real hardware.

---

## Recommendation: Filament, single core dependency + a locally-compiled material asset (no second runtime dependency)

**Add to `gradle/libs.versions.toml`** (the `filament = "1.56.5"` version and `filament-android` library entry are already staged there, unused in `app/build.gradle.kts` — likely left over from the interrupted WIP checkpoint):

```
implementation(libs.filament.android)   // com.google.android.filament:filament-android:1.56.5
```

That one AAR is the ceiling I'd spend. I'd avoid adding `gltfio-android` as a second dependency: it's tempting as a source of a "free" ubershader material, but its `MaterialProvider`/`UbershaderProvider` is designed around gltfio's own glTF-loading pipeline, and I'm not confident enough (without having run it) that it's a supported, stable way to get a standalone `MaterialInstance` for a hand-built renderable outside that pipeline. Filament's own official Android sample ("hello-triangle") renders a real shaded object with `filament-android` alone, by compiling a minimal material once with `matc` (Filament's standalone material compiler binary, downloaded from the Filament GitHub releases — not a Gradle plugin, not NDK/CMake, not a new IDE toolchain) and checking the compiled `.filamat` blob into the repo as a static asset (e.g. `app/src/main/assets/materials/unlit.filamat`), loaded at runtime via `Material.Builder().payload(...)`. This is the well-precedented, lower-risk path versus the gltfio route, so it's what I'd commit to for this milestone.

**Geometry/material plan to satisfy "an actual visible 3D object":** a single procedurally defined mesh (e.g. a unit cube or icosahedron) built from inline vertex/index arrays in Kotlin via `VertexBuffer`/`IndexBuffer`/`RenderableManager`, shaded with the one compiled unlit/lit material above. Zero imported models or textures — this trivially clears the asset-licensing bar since there is no external asset beyond a compiled shader program you wrote yourself.

**Main trade-off I'm accepting:** running `matc` is a one-time, non-Gradle, manual binary step (platform-specific tool, its output committed as a binary asset) rather than something Gradle resolves automatically. The engine milestone needs to document which `matc` build was used and keep the source `.mat` file next to the compiled output so it's reproducible — this is a real manual-process dependency the orchestrator should be aware of, even though it touches no build file this task isn't scoped to edit.

**Performance:** Filament's render loop is a persistent GL context; even a static single-object scene costs continuous Choreographer-driven frame submission. For a mostly-static scene with occasional animated accents, the engine should render on-demand (invalidate/request a frame only when something changes, pause the loop in `onPause`/`onStop`) rather than free-running at 60fps, to keep idle thermal/battery cost near zero. I have not measured this on a physical mid-range device — treat the budget as unverified until it's profiled there, not the emulator.

**Accessibility:** the Filament surface mounts via `AndroidView` inside Compose and must be marked non-accessible/decorative (e.g. cleared semantics) so TalkBack skips the opaque render; every interactive control stays a real Compose composable positioned over/beside it. Reduced motion means: no continuous rotation/camera motion, a single static lit object — satisfiable trivially with this minimal scene.

**Automated verification:** `agent/visual_qa.py` already expects an `engine-canvas` test tag for this exact milestone and only interacts via the accessibility tree (uiautomator dump), so it never needs to "see" the GL surface itself — it just needs the wrapping composable to carry `Modifier.testTag("engine-canvas")` and report `enabled="true"` in the dump. Worth flagging as an unverified detail: a plain non-clickable `AndroidView` wrapper may or may not report `enabled=true` by default in the dump; the implementing milestone should confirm this empirically on the emulator rather than assume it.

**Confidence:** this is a working recommendation for the next bounded milestone, not a verified result — I haven't run Filament on real hardware or confirmed the `matc`-compiled-material path compiles clean end-to-end in this exact project; the implementing milestone should treat both the frame-time budget and the `enabled` semantics detail above as open risks to close first.
