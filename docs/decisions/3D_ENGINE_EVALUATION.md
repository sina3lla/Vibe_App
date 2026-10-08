# 3D engine evaluation — 2026-10-08

Captured verbatim from the design-phase agent response below. This is a working recommendation for the controller to act on next, not an owner-approved architecture decision or a claim that the chosen approach has been benchmarked on real hardware.

---

## Recommendation: Google Filament (`com.google.android.filament:filament-android`)

**Dependency to add** (version catalog + one line in `app/build.gradle.kts`):

```toml
# gradle/libs.versions.toml
[versions]
filament = "1.56.5"  # verify against Maven Central before pinning — I have no live network access to confirm this is current

[libraries]
filament-android = { group = "com.google.android.filament", name = "filament-android", version.ref = "filament" }
```

```kotlin
// app/build.gradle.kts
implementation(libs.filament.android)
```

That's the entire integration cost: one prebuilt AAR (native `.so`s are bundled inside it), no CMake/NDK project, no second IDE toolchain, no AR/ARCore transitive pull-in (unlike `sceneview-android`, which wraps Filament but drags in ARCore and extras this milestone doesn't need).

### Why this fits each constraint

- **Performance**: Filament is a tile-based, PBR forward/deferred renderer built for mobile; you can run its `Choreographer` loop on-demand (render only when the scene actually changes) rather than continuously, which matches the brief's "mostly-static scene with occasional animated accents" framing and keeps thermal/battery cost close to the static-scene case rather than the persistent-scene case. This still needs to be *measured*, not assumed.
- **Accessibility / controller compatibility**: Filament only owns a rendering surface (`SurfaceView`/`TextureView`), not input or UI. The scene is hosted via `AndroidView` inside a Compose `Box`; every tappable control stays a real Compose composable layered on top with `Modifier.testTag(...)`, so TalkBack and `agent/visual_qa.py`'s resource-id tap automation keep working untouched. The script already reserves an `engine-canvas` tag for this milestone — the Filament surface itself should carry that tag.
- **Asset licensing**: Start with code-generated primitive/procedural geometry (spheres, extruded shapes, simple glTF built at build time if needed) rather than importing third-party `.glb`/`.fbx` models, avoiding the temptation CURRENT_TASK flags. Core `filament-android` alone is a few MB; avoid adding `gltfio-android`/`filament-utils` unless an actual asset pipeline is approved, to keep APK size down.
- **Automated verification**: No new verification mechanism — same adb/uiautomator screenshot-and-tap journey, same testTag contract.
- **Integration cost**: Single Gradle coordinate, no native build system.

### Trade-off accepted
Filament brings real engine complexity (materials, lighting, fog, camera) versus a bare `GLSurfaceView` + hand-rolled OpenGL ES, which would have zero dependency footprint but would require reimplementing PBR/lighting/fog from scratch to achieve the "magical surreal" look and the dual bright/dark scene lighting requirement in `WORLD_DESIGN.md`. Filament's built-in lighting/fog/material system directly serves that requirement at the cost of added APK size (needs real measurement, likely several MB before ABI splitting) and a steeper learning curve than raw GL.

### Confidence
This is a paper evaluation only — I have not run Filament on any device or emulator in this repo, so frame-time, thermal, and actual APK-size numbers are unverified. The next milestone should land a minimal scene (a few lit primitives, on-demand render loop, one Compose button overlay tagged `engine-canvas`) and profile it on a real mid-range device before any further 3D investment. Treat this as a working recommendation for that milestone, not an approved architecture.
