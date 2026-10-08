# `filamat-android` — verified version and integration reference

Status: a stable reference document, not a decision record. Unlike `docs/decisions/3D_ENGINE_EVALUATION.md`, **the controller never overwrites this file** during the engine milestone's design phase — it is safe to cite across runs. If a future milestone changes the engine approach, update this file explicitly rather than leaving it to rot; do not assume it is still accurate without rereading it.

## Why this file exists

Codex's BLOCKED review of `agent/runs/20261008-232956/engine-1-review.json` found that `docs/decisions/3D_ENGINE_EVALUATION.md` named `com.google.android.filament:filamat-android` as necessary but left its version unverified, and that the actual scene only ever rendered a Filament `Skybox` (background) plus a **Compose `Canvas`-drawn cube standing in for the real object** — not native geometry. This document supplies the missing verified version so that gap stops recurring, and states plainly what still has to be built and proven.

## Verified coordinates

```
com.google.android.filament:filamat-android:1.56.0
```

**This is the same exact version already pinned for `filament-android`.** Verified 2026-10-08 against:

1. Maven Central's official metadata: `https://repo.maven.apache.org/maven2/com/google/android/filament/filamat-android/maven-metadata.xml` (HTTP 200) lists `1.56.0` among published versions, with `<latest>`/`<release>` both `1.77.2` at fetch time.
2. Direct artifact resolution: `filamat-android-1.56.0.pom` and `.aar` both return HTTP 200 from `repo.maven.apache.org`.
3. The POM (`com.google.android.filament:filamat-android:1.56.0`) declares `packaging=aar`, Apache-2.0 license, source at `https://github.com/google/filament`, and one runtime dependency (`androidx.annotation:annotation:1.9.0`) — no conflict with this project's existing dependencies.
4. API confirmed directly against the `v1.56.0` git tag source tree (`android/filamat-android/src/main/java/com/google/android/filament/filamat/MaterialBuilder.java` and `MaterialPackage.java`), not from memory or documentation alone.

Do **not** guess a different patch version from memory, and do not use a dynamic/wildcard version — `agent/loop.py`'s `find_dynamic_versions()` will fail the build before Gradle even runs if one appears in `gradle/libs.versions.toml`/`app/build.gradle.kts`.

## Required initialization

`MaterialBuilder`'s class-static block calls `System.loadLibrary("filamat-jni")` automatically on first class load — no manual `loadLibrary` call needed for that specific native library. However, **the builder's own native subsystem is a separate, explicit lifecycle that must be started before first use**:

```kotlin
// Once per process, before the first MaterialBuilder() is constructed. Guard with a
// static/companion-object flag — calling init() more than once, or creating a
// MaterialBuilder before init(), is undefined behavior per the upstream Javadoc/source.
MaterialBuilder.init()
// ... build one or more materials ...
MaterialBuilder.shutdown()  // once, when permanently done (process/Engine teardown) — not per-recomposition
```

**Thread-safety constraint (from `MaterialBuilder.build(Object)`'s own Javadoc):** "If you are using Filament and the filamat library together you *must* pass an `Engine` as the job system provider, *or* invoke `MaterialBuilder` from a thread other than the thread used to invoke Filament APIs." The simplest correct choice for a single-threaded Compose harness: always call `.build(engine)` passing the same `Engine` instance already used for rendering, on the same thread — never call `.build()` (no-arg) or `.build(null)` from that thread.

## Integration sequence (verified against the `v1.56.0` source)

1. **Compile the material once** (e.g. at harness setup, not per frame/recomposition):
   ```kotlin
   val pkg: MaterialPackage = MaterialBuilder()
       .platform(MaterialBuilder.Platform.MOBILE)
       .targetApi(MaterialBuilder.TargetApi.OPENGL)
       .optimization(MaterialBuilder.Optimization.NONE) // fine for one tiny unlit material; revisit for release
       .shading(MaterialBuilder.Shading.UNLIT)
       .material(
           "void material(inout MaterialInputs material) {" +
           "    prepareMaterial(material);" +
           "    material.baseColor = vec4(1.0, 0.6, 0.2, 1.0);" +
           "}"
       )
       .build(engine) // pass the existing Engine — see thread-safety note above
   check(pkg.isValid()) { "MaterialBuilder produced an invalid package" }
   ```
   `MaterialPackage.getBuffer(): ByteBuffer` and `.isValid(): Boolean` are the only two members — confirmed from source, not assumed.

2. **Build the real `Material`** (from the already-present base `filament-android` library, not `filamat-android`):
   ```kotlin
   val material = Material.Builder()
       .payload(pkg.buffer, pkg.buffer.remaining())
       .build(engine)
   val materialInstance = material.defaultInstance
   ```
   `Material.Builder.payload(Buffer, Int)` and `.build(Engine)` confirmed from `Material.java` at the same tag.

3. **Attach real geometry and material to a renderable** (procedural cube `VertexBuffer`/`IndexBuffer`, as already planned in `docs/decisions/3D_ENGINE_EVALUATION.md` — no change needed to the geometry source, only to what material backs it):
   ```kotlin
   RenderableManager.Builder(1)
       .boundingBox(Box(0f, 0f, 0f, 0.5f, 0.5f, 0.5f))
       .geometry(0, RenderableManager.PrimitiveType.TRIANGLES, vertexBuffer, indexBuffer)
       .material(0, materialInstance)
       .build(engine, entity)
   scene.addEntity(entity)
   ```
   `RenderableManager.Builder.geometry(int, PrimitiveType, VertexBuffer, IndexBuffer)`, `.material(int, MaterialInstance)`, and `.build(Engine, int)` all confirmed from `RenderableManager.java` at the same tag.

4. **Tear down in the reverse order** the harness already tears down its `Engine`/`Renderer`/`Scene` (destroy the renderable's entity, the `Material`, then call `MaterialBuilder.shutdown()` once — not per-recomposition, mirroring `init()`).

## Acceptance — what this milestone must actually demonstrate

Per the owner's explicit clarification: **the normal engine scene must show actual native-rendered geometry** (a `RenderableManager`-backed object built from the material pipeline above, drawn by Filament itself). A Compose `Canvas`-drawn 2D substitute is a legitimate **accessibility/fallback** path (and must still exist for when the native pipeline genuinely cannot initialize — e.g. on a device/emulator without the needed GL/Vulkan support), but it is not evidence the 3D pipeline works and cannot be presented as satisfying this milestone. A screen reading "native pipeline unavailable" is a valid *fallback* state, not a pass.

The implementing agent must:
- Expose a machine-checkable, honest status signal distinct from `engine-canvas` itself — e.g. a semantics node tagged `engine-render-status` whose text/content-description is exactly `"native"` when `pkg.isValid()` was true and the `RenderableManager` entity was actually added to the `Scene`, or exactly `"fallback"` otherwise. `agent/visual_qa.py`'s `engine` journey checks this tag and fails the automated gate if it is missing or reads anything other than `"native"` — this is a mechanical check, not only a judgment call left to Codex or to the agent's own completion report.
- Write a completion report that states plainly which state was actually reached (native or fallback) and why, never claiming "the pipeline renders" or "verified end-to-end" when the evidence shows a fallback or an unverified claim. Overclaiming here is exactly what the prior cycle's review (`agent/runs/20261008-232956/engine-1-review.json`) flagged and blocked on.
