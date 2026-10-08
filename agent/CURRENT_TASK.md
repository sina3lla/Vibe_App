# Current Task — add the selected 3D rendering dependency and a minimal harness

Read docs/decisions/3D_ENGINE_EVALUATION.md (just written by the controller from the prior design-phase response) and docs/PRODUCT_VISION.md/docs/WORLD_DESIGN.md for the magical-surreal creative direction. Froopyland is a tone reference only, never a copied asset/character source.

## Build now
Add exactly the recommended dependency to app/build.gradle.kts and, if it uses the version catalog, to gradle/libs.versions.toml. These are the only two files outside app/src/main, app/src/test, and app/src/androidTest you may touch this milestone — no other Gradle file, no wrapper, no settings.gradle.kts, no plugin changes beyond what the recommendation requires.

Build a minimal placeholder 3D scene harness proving the pipeline renders inside the existing Compose shell: one simple ambient/idle low-poly placeholder object (your own simple geometry, not a copied or unlicensed asset), with ordinary Compose UI (not raw GL) carrying any interactive controls. Respect reduce-motion: provide an idle state with no required continuous animation, and a text/non-spatial fallback that does not depend on the 3D surface rendering at all. No territory content, no chatbot, no journaling or reflection flow — this milestone only proves the engine choice is viable and automatable.

Expose a stable Compose test tag `engine-canvas` on the harness's own screen (or on whatever existing screen hosts it) via semantics testTagsAsResourceId, so agent/visual_qa.py's `engine` journey can find and screenshot it. If no interactive control is needed yet, a visible placeholder scene with that tag is sufficient evidence.

Add a minimal JVM or instrumentation test asserting the harness composable does not crash on first composition and that its non-spatial fallback is reachable without the 3D surface.

## Completion
All app code for this milestone, not just a plan or mockup. Orchestrator runs checks; do not attempt shell tools. Report files changed, design decisions, and limits honestly. You may edit only app/src/main, app/src/test, app/src/androidTest, and exactly app/build.gradle.kts, gradle/libs.versions.toml — no other script, doc, or build file. The supervising agent continues the full build after this milestone; do not claim launch readiness.

## Execution owner
The owner started this automated loop from Android Studio. Your current role is bounded implementation of this one milestone; do not launch other agents, loops, or milestones. The controller advances automatically once this milestone's checks and review pass; it never publishes, pushes, deploys, or spends on services on its own.
