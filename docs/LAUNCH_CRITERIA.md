# Launch Criteria

A PASS on one task does not mean launch-ready. Record evidence for every gate below; missing evidence is NOT VERIFIED, never an implicit pass.

## Build and reliability
- `./gradlew assembleDebug test lintDebug assembleRelease` succeeds at the reviewed revision.
- Core navigation and every approved practice journey complete without crashes or dead ends.
- Meaningful tests cover ritual transitions, relevant state restoration, and regressions; sample arithmetic tests do not establish coverage.
- Backgrounding, return, rotation, and process recreation have explicit verified behavior. Audio and camera release correctly; no unexpected restart of sound.

## Product completeness
- At least one appropriately sourced and reviewed practice is implemented end to end: guided entry, explained recommendation, informed start, paced steps, pause/skip/exit, intentional finish, and optional feedback. A user who does not know which exercise to choose can complete the journey.
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
- The owner reviews fidelity to the product purpose; practice content has documented sources, limitations, alternatives, and appropriate review. Technical review does not certify therapeutic effectiveness or safety. Clinical claims, if proposed, receive appropriate evidence and specialist review before release.
- Child-facing and parenting-specific content is excluded from this first adult release.

## Guided recommendation quality
- Every entry answer, including “I’m not sure,” has an understandable path. Recommendation rules are inspectable and tested.
- Suggested practices explain why they fit, what the user will do, duration, and realistic expectations before starting. Users can choose an alternative.
- No-change, discomfort, and unsure feedback produce respectful next steps without blame, pressure, or automatic escalation of intensity.

## Authentication and Terms & Conditions (AGB)
- User login is implemented, including appropriate recovery, sign-out, expired-session, cancellation, network-failure, and invalid-input states for the selected login method.
- Before authenticated access, the user explicitly accepts the applicable AGB. The acceptance control is not preselected; the full terms are readable and available in the selected language before acceptance. Declining must not count as acceptance.
- Acceptance records are associated with the account and include terms version, acceptance timestamp, and presented language. Session restoration or another device cannot bypass the acceptance gate. Valid existing acceptance avoids unnecessary repeated prompts.
- Changed terms and re-acceptance behavior are specified and tested. Legal text is versioned and reviewed for the selected launch markets; an agent-generated draft alone does not satisfy launch readiness.
- Privacy information is accessible and distinct from AGB acceptance. Optional permissions/marketing choices are not silently bundled into acceptance.
- Authentication credentials and tokens are handled securely; account-data retention and deletion behavior are defined and tested. No raw secrets in logs or source control.

## Language and European launch scope
- A finite launch-country and supported-language matrix is agreed and recorded before launch. English is required; other European launch languages must be explicitly named.
- On first use, the user must choose a supported language before onboarding/terms. The choice persists across restarts and authenticated sessions and can be changed in settings. Cross-device preference behavior is defined and tested.
- Every supported language covers the entire shipped app: authentication, recovery, guided entry, recommendations, practices, feedback, settings, errors, accessibility labels, any notifications/audio, and legal screens.
- UI and practice content update consistently after a language change. No hard-coded prototype text or unintended mixed-language content remains in supported locales. Formatting and plurals respect the selected locale.
- Test each supported locale end to end, including login, AGB decline/accept/re-accept, practice completion, language switching, relaunch, and sign-out/sign-in. Verify text expansion, large fonts, accents, and relevant scripts without clipping.
- Missing translations fail the release content check; unsupported-device-language fallback is explicit and tested. Each legal translation maps to the applicable terms version.
- European launch readiness includes documented review of the actual account/data practices and product claims for the chosen markets. This checklist is a product requirement, not a claim of legal compliance.
