<!--
Controller-generated. agent/loop.py overwrites this file at the start of each
milestone from agent/milestones.py — hand edits here are lost the next time the
loop runs. Edit the milestone briefs in agent/milestones.py instead; the Claude
subprocess the loop launches is denied Edit/Write on agent/** so it cannot
rewrite its own acceptance criteria mid-cycle (see CLAUDE.md's execution
boundary and agent/loop.py's claude() settings deny-list).

The content below is the first milestone ("engine") in the current sequence,
shown here so the repository is accurate when no loop is running. See
agent/README.md for the full milestone order and how to resume mid-sequence.
-->

# Current Task — evaluate an Android 3D approach (design phase, read-only)

The owner has confirmed the new creative direction: an original, magical, explorable 3D world with surreal environments and playful, discovery-driven interaction. Froopyland (Rick and Morty) is a conceptual tone reference only — strange, shifting, inventive — never a source of artwork, characters, or environments to copy or imitate. There is no reflection flow, journaling prompt, emotional debrief, chatbot, or educational video; understanding still has to emerge through interaction, with optional brief explanations in context, exactly as before.

You cannot write files in this phase. Read CLAUDE.md, docs/PRODUCT_VISION.md, docs/WORLD_DESIGN.md, docs/LAUNCH_CRITERIA.md, app/build.gradle.kts, gradle/libs.versions.toml, and agent/visual_qa.py (to understand how the controller taps controls by Compose testTag today).

## Evaluate
Recommend exactly one Android 3D rendering approach for this project and the specific dependency coordinates/version you would add. Weigh, at minimum:
- **Performance**: frame-time budget on a mid-range device; thermal/battery cost of a persistent 3D scene versus a mostly-static one with occasional animated accents.
- **Accessibility**: a raw GL/Filament surface is not itself accessible to TalkBack or to the controller's resource-id-based tap automation — interactive controls must stay as real Compose composables overlaid on the 3D view (or expose equivalent invisible semantics nodes at the same screen position), and a non-spatial/reduced-motion fallback must remain possible without losing the core interaction.
- **Asset licensing**: original or properly licensed low-poly/procedural assets only; flag any approach that would tempt importing unlicensed third-party models, and note the APK-size cost of any embedded assets.
- **Automated verification**: whether the controller's adb/uiautomator screenshot-and-tap journey (agent/visual_qa.py) can still drive it — this must not require a new, separate verification mechanism.
- **Integration cost**: one Gradle dependency change (plus version catalog entry) is the acceptable ceiling for this milestone; do not recommend an approach needing a native build system (CMake/NDK) or a second IDE toolchain unless no simpler option meets the above criteria.

State your single recommendation plainly, the exact Gradle coordinate(s)/version, and the main trade-off you accepted. This is a working recommendation for the next bounded milestone to implement, not an owner-approved architecture decision — say so if your confidence is limited by not having run anything on real hardware.

## Completion
All app code for this milestone, not just a plan or mockup. Orchestrator runs checks; do not attempt shell tools. Report files changed, design decisions, and limits honestly. You may edit only app/src/main, app/src/test, app/src/androidTest. Do not edit scripts/docs/build files. The supervising agent continues the full build after this milestone; do not claim launch readiness.

## Execution owner
The owner started this automated loop from Android Studio. Your current role is bounded implementation of this one milestone; do not launch other agents, loops, or milestones. The controller advances automatically once this milestone's checks and review pass; it never publishes, pushes, deploys, or spends on services on its own.
