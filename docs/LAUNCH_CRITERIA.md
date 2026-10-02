# Launch Criteria

A PASS on one task does not mean launch-ready. Record evidence for every gate below; missing evidence is NOT VERIFIED, never an implicit pass.

## Build and reliability
- `./gradlew assembleDebug test lintDebug assembleRelease` succeeds at the reviewed revision.
- Core navigation and all three journeys complete without crashes or dead ends.
- Meaningful tests cover ritual transitions, relevant state restoration, and regressions; sample arithmetic tests do not establish coverage.
- Backgrounding, return, rotation, and process recreation have explicit verified behavior. Audio and camera release correctly; no unexpected restart of sound.

## Product completeness
- All journeys in PRODUCT_VISION.md work, including Ascension denial, simulated mode, completion, and restart.
- Every visible control works and gives feedback. Relevant empty, error, loading, and success states are intentional.
- No placeholder content or unsupported factual claims. Optional camera has a clear explanation and graceful fallback.

## Visual and interaction quality
- Fresh screenshots from the built APK cover Home, Vibrant, Mannequin, Ascension prompt, simulated ritual, and completion.
- Review normal portrait, compact 320–360 dp width, landscape, and 200% font size. No clipping, inaccessible actions, overlap with system UI, or illegible text on moving backgrounds.
- Verify light and dark system themes with the app's deliberate dark palette; inspect gesture and three-button navigation.
- Spacing, type, colors, control states, and motion form one deliberate design language. Review screenshots directly, not only source code.
- Back dismisses dialogs before navigating; essential controls are reachable without precise tapping or motion.

## Accessibility, privacy, and performance
- Screen-reader labels, focus order, meaningful state announcements, and accessible alternatives to canvas hotspots work. Verify touch targets and readable contrast.
- Camera remains optional and local; no recording, upload, secrets, signing keys, or production data in the repo.
- Audio volume and interruption behavior are controlled. Core interactions stay responsive; inspect startup and sustained animation on an emulator and a physical device before release.

## Evidence and release boundary
Maintain a launch checklist with gate, device/configuration, command or journey, result, and evidence path. Automated screenshots establish only the states they actually exercised. TalkBack, physical-device performance, camera hardware behavior, and the full configuration matrix remain open until specifically verified.

Codex returns task PASS only when the task's acceptance criteria and required checks pass. Final launch review covers this entire document. Release signing, store upload, purchase, deployment, and public claims require owner action; the autonomous loop never performs them.
