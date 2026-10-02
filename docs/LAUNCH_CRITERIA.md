# Launch Criteria

A PASS on one task does not mean launch-ready. Record evidence for every gate below; missing evidence is NOT VERIFIED, never an implicit pass.

## Build and reliability
- `./gradlew assembleDebug test lintDebug assembleRelease` succeeds at the reviewed revision.
- Core navigation and every approved practice journey complete without crashes or dead ends.
- Meaningful tests cover ritual transitions, relevant state restoration, and regressions; sample arithmetic tests do not establish coverage.
- Backgrounding, return, rotation, and process recreation have explicit verified behavior. Audio and camera release correctly; no unexpected restart of sound.

## Product completeness
- At least one owner-specified somatic practice is implemented end to end: intention, informed start, paced steps, pause/skip/exit, intentional finish, and optional observation. The content gate in PRODUCT_VISION.md is resolved.
- Every visible control works and gives feedback. Relevant empty, error, loading, and success states are intentional.
- No placeholder exercise content, unsupported treatment claims, or certainty about hidden intentions. Founder experience is distinguished from a universal promise. No retained prototype feature conflicts with the approved purpose.

## Visual and interaction quality
- Fresh screenshots from the built APK cover the approved practice journey, including choice, instructions, active step, pause/exit, and completion. Current prototype screenshots validate infrastructure only; they do not satisfy this launch gate.
- Review normal portrait, compact 320–360 dp width, landscape, and 200% font size. No clipping, inaccessible actions, overlap with system UI, or illegible text on moving backgrounds.
- Verify light and dark system themes with the chosen app palette; inspect gesture and three-button navigation.
- Spacing, type, colors, control states, and motion form one deliberate design language. Review screenshots directly, not only source code.
- Back dismisses dialogs before navigating; essential controls are reachable without precise tapping or motion.

## Accessibility, privacy, and performance
- Screen-reader labels, focus order, meaningful state announcements, and accessible alternatives to canvas hotspots work. Verify touch targets and readable contrast.
- No unnecessary camera or microphone access. Any retained camera remains optional and local. No recording, upload, secrets, signing keys, or production data in the repo. Optional sensitive observations have explicit retention and deletion behavior.
- Audio volume and interruption behavior are controlled. Core interactions stay responsive; inspect startup and sustained animation on an emulator and a physical device before release.

## Evidence and release boundary
Maintain a launch checklist with gate, device/configuration, command or journey, result, and evidence path. Automated screenshots establish only the states they actually exercised. TalkBack, physical-device performance, camera hardware behavior, and the full configuration matrix remain open until specifically verified.

Codex returns task PASS only when the task's acceptance criteria and required checks pass. Final launch review covers this entire document. Release signing, store upload, purchase, deployment, and public claims require owner action; the autonomous loop never performs them.

## Agency and content review
- The user can decline, pause, skip, or stop a practice without shame, pressure, or loss of standing. Completion never requires claiming to feel better.
- No infallible manipulation/hate detector, guaranteed calm, or implied diagnostic assessment. Social examples distinguish observations, interpretations, and choices.
- The owner reviews fidelity to the supplied practice. Technical review does not certify therapeutic effectiveness or safety. Clinical claims, if proposed, receive appropriate evidence and specialist review before release.
- Child-facing and parenting-specific content is excluded from this first adult release.
