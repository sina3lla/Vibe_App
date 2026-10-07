# Full app implementation plan

The owner explicitly requested the full build, superseding the first-slice-only stop. Continue between milestones without mandatory taste approval. Scope remains bounded per agent invocation; never bypass permissions or a failed check.

## Milestones
0. Evaluate and select an Android 3D rendering approach for the magical, surreal, explorable world now confirmed as the creative direction (see docs/PRODUCT_VISION.md). A read-only design phase weighs performance, accessibility (TalkBack and the controller's own tap automation both need real Compose controls, not an opaque GL surface), asset licensing, and automated-verification compatibility, and names one approach; a second, explicitly scoped phase adds exactly that one Gradle dependency plus a minimal placeholder harness proving it renders and is automatable. This is the only milestone permitted to touch app/build.gradle.kts or gradle/libs.versions.toml, and only those two files.
1. Complete explorable product shell and five connected territories: attention, wants/needs, boundaries, interpretation, rest/ambition. Each has a distinct educational manipulation, optional concise explanation, accessible alternatives, and saved discoveries. Replace obsolete ritual entry routes.
2. Settings and persistence: System/Bright/Dark, quiet motion, language, personal-data controls; robust navigation and restoration. Implement English and a second locale after owner's language choice.
3. Account and legal flows: integrate the existing provider if supplied; otherwise implement an explicit unconfigured integration boundary and truthful local preview. Do not pretend local profiles are authenticated accounts, collect passwords without a backend, or label draft legal text legally approved. Production authentication/legal review remain release blockers until resolved.
4. Localization and content review: complete supported strings, source and review explanatory content, avoid diagnostic or efficacy claims.
5. Build/test/lint/release compilation, meaningful device tests, fresh visual/interaction evidence for all territories, themes, localization, data lifecycle. Repair actual findings through Claude → Codex → Claude.
6. Produce installable debug APK and an honest launch checklist showing passing and blocked gates. No public release or payments.

## Working scope
Keep the existing Compose stack as the app shell, navigation, and the surface for every interactive control; milestone 0 may add one evaluated 3D rendering dependency for the world itself, and no other milestone changes dependencies. No multiplayer, video courses, chatbot, cloud inference, reflection/journaling flows, or emotional debriefs. Choose a coherent spatial interface rather than a conventional course-card dashboard. A tone reference to another work (e.g. Froopyland) is conceptual only, never a source of copied artwork or characters. Working brand FeelAnything; final brand remains open.

## Progress
- Initial planning complete; implementation and verification pending.
- Existing connected navigation regression still needs emulator execution.
- Full cycle not yet verified.
- 2026-10-06: owner confirmed the magical/surreal/explorable 3D creative direction and authorized an evaluated 3D rendering approach; milestone 0 above and agent/milestones.py's `engine` milestone were added accordingly. No 3D library has actually been chosen or added yet — that happens the first time the loop runs milestone 0.

## Owner clarification — execution and login
The assistant only co-creates Markdown and provides start instructions. The owner starts the Claude–Codex loop in Android Studio. Keep agent/STOP until the owner deliberately starts it; do not resume automatically.

Authentication reference supplied: https://github.com/Lunatreon/FeelY, app/api/routes/auth.py. Read docs/AUTH_INTEGRATION.md. Existing account backend is identified; deployed endpoint, mobile configuration, and versioned terms acceptance still require verification. Do not build a separate fake account system.
