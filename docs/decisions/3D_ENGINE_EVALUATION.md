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

---

## Controller-verified dependency pin (preparation session, 2026-10-08)

**What happened:** the design recommendation above named `1.56.5`, and an interrupted implement/buildfix cycle (`agent/runs/20261008-223002`) carried that version into `gradle/libs.versions.toml` without checking it against Maven. Gradle's resolution failed — `1.56.5` does not exist on Google's Android repo or Maven Central — and the automated repair attempt (correctly denied by the workspace restriction) tried to `Glob` search `/Users/lelu` for a copy of the artifact instead of checking the real source of truth. Both the unverified pin and the out-of-workspace search were defects in process, not anything to do with Filament itself.

**Verification actually performed in this preparation session** (network access available here; not available to the sandboxed loop Claude):

1. Fetched `https://repo.maven.apache.org/maven2/com/google/android/filament/filament-android/maven-metadata.xml` directly (`curl`, HTTP 200, `<lastUpdated>20261008184915</lastUpdated>`). `1.56.5` is **absent** from the `<versions>` list; the nearest real entries are `1.56.0` and `1.57.1`. Latest/release at fetch time: `1.77.2`.
2. Confirmed `1.56.0`'s artifacts actually resolve: `filament-android-1.56.0.pom` and `.aar` both return HTTP 200 from `repo.maven.apache.org` (Google's `dl.google.com` mirror returns 404 for this artifact at every version checked — this project's `settings.gradle.kts` already lists both `google()` and `mavenCentral()` in `dependencyResolutionManagement`, and the original failing Gradle log shows it searching both locations, so Maven Central alone resolving it is sufficient).
3. Cross-checked `https://raw.githubusercontent.com/google/filament/main/RELEASE_NOTES.md` at the `google/filament` GitHub repo: `v1.56.0`'s only noted change is `backend: descriptor layouts distinguish samplers and external samplers [New Material Version]` — a material-compiler/backend concern, not a Java/Kotlin public-API removal. Note for future reference: several patch versions appear in that file's historical log (e.g. `1.56.1`–`1.56.8`) that are **not** published to Maven at all — a git tag/release note existing is not proof an Android artifact was published; Maven metadata is the only authoritative source for "does this resolve."
4. Confirmed API surface compatibility directly against the `v1.56.0` source tag (`api.github.com/repos/google/filament/contents/...?ref=v1.56.0`): `Engine`, `Camera`, `Renderer`, `Scene`, `Skybox`, `View` all present under `android/filament-android/src/main/java/com/google/android/filament/`, and `UiHelper`, `DisplayHelper` present under the nested `.../filament/android/` package — i.e. every class `EngineHarness.kt` actually uses exists at this exact version.

**Decision:** pinned `gradle/libs.versions.toml`'s `filament` version to the exact string `"1.56.0"` — verified-resolvable, verified API-compatible with the harness as already written, and the closest real release to the originally recommended `1.56.x` family (deliberately not jumping to the newest `1.77.2`, which was published the same day this was checked and has ~20 minor versions of unreviewed drift against the only-ever-recommended-from-memory API usage above).

**Still unverified — needs the real build/device:**
- Whether `1.56.0` actually compiles clean against this project's AGP/Kotlin/compileSdk versions (Maven resolution succeeding is necessary, not sufficient).
- The `matc`-compiled-material path described above (no `matc` run has happened; the material-version note above applies if a later milestone ever upgrades Filament without recompiling that asset).
- Frame-time/thermal budget and the `engine-canvas` `enabled` semantics detail, both already flagged as open above.

**Process fix, not just a data fix:** `agent/loop.py`'s build-repair step now fails fast (before spending a Gradle run) if `gradle/libs.versions.toml`/`app/build.gradle.kts` contain a dynamic version (`+`, `latest.release`, `latest.integration`), and the engine milestone's briefs now require any version recommendation or repair to be an exact pin with a stated verification source — reporting a missing-verification gap explicitly rather than guessing or searching outside the repository. See `agent/milestones.py` and `agent/tests/test_loop.py`'s `DynamicVersionGuardTests`.
