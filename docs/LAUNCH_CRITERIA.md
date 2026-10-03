# Quality Gates — prototype and release

Status: draft. The product direction is established; the release scope still needs a finite content and locale list. Missing evidence is NOT VERIFIED, never a pass. These are product requirements, not a legal-compliance certification.

## A. Prototype task gate
Apply only the current task's bounded acceptance criteria plus these essentials:
- The playable interaction works, its educational purpose is understandable, and the visitor has meaningful choice.
- The actual screen implements exploration, not a disguised linear session, chatbot, video course, or static explanation gallery.
- Model behavior is not presented as measurement of the user's body or mind.
- Back/exit works; necessary controls remain available with reduced motion, large text, and an accessible alternative to spatial gestures.
- Relevant build, tests, lint, interaction checks, and fresh visual evidence pass for the changed artifact. A mockup is labeled as such and cannot stand in for a tested APK.
- No evidence or test results are invented. Evidence reflects the current revision.

Login, complete translation coverage, payment integration, and the full world are not prerequisites for an internal interaction prototype unless its task specifically addresses them.

## B. Release scope and product quality
- Agree a finite release map and encounter list. Every included encounter has a complete content record, useful interactions, accurate explanations, and clear exit behavior.
- People can enter, discover an interaction, understand its purpose, move elsewhere, leave, and return. Optional navigation help does not require identifying a diagnosis or choosing a technique.
- Observe representative people using the app without continuous coaching. Record misunderstandings and resolve issues that prevent understanding or choice. Usage observation is not evidence of therapeutic benefit.
- No dead controls, unexplained gates, filler environments, mandatory emotional improvement, or rewards for reporting distress.
- Screenshots and interaction recordings cover entry, exploration, explanations, alternatives, exits, and return. Inspect more than still imagery: sequence, responsiveness, and discoverability matter.

## C. Reliability and accessibility
- Debug/release builds, unit tests, lint, and relevant connected Android tests pass at the release revision. Tests cover actual behavior, not sample arithmetic.
- Navigation, selection, saved discoveries, activity/process recreation, backgrounding, and resumption behave intentionally. Sound never restarts unexpectedly.
- Check compact phones, supported orientations, 200% text, system insets, supported app themes, and both gesture and three-button navigation. Define unsupported orientations explicitly.
- TalkBack order, labels, state feedback, usable contrast/touch targets, and non-spatial alternatives are verified. Motion/audio can be reduced or disabled without losing core learning.
- Verify startup and sustained interactions on a physical device as well as the emulator. Set and document measurable performance budgets for the actual world before release.

## D. Content and agency
- Factual psychological/body explanations have documented sources and appropriate review; simplified metaphors disclose their limits where relevant.
- No diagnostic conclusions, guaranteed calm, inferred hidden motives, or claims of trauma treatment. Calling the product self-help does not excuse unsupported claims.
- Panic-related content has appropriate review, a usable stop/support route, and does not assume unfamiliar symptoms are necessarily panic. Do not manufacture distress to demonstrate a mechanism.
- The person can disagree, ignore, or leave. Personal observations are optional. Technical PASS is not clinical validation.

## E. Account and AGB — confirmed release requirements
- Login, sign-out, recovery appropriate to the chosen method, expired-session and error states work.
- Before authenticated product access, explicit unselected-by-default acceptance of applicable Terms & Conditions/AGB is required. The full terms are available in the selected language first; declining is not acceptance.
- Record account, accepted terms version, time, and presented language. Restored sessions and another device cannot bypass required acceptance. Valid existing acceptance avoids repeated signing on every login.
- Define and test changed-terms/re-acceptance behavior. “Sign” currently means affirmative acceptance; no special signature technology has been selected.
- Legal text and translations are reviewed for the chosen markets. Privacy information is distinct; optional marketing is not bundled into terms acceptance.
- Define secure authentication handling, minimum account data, retention, deletion, and any cross-device synchronization. No credentials or sensitive observations in diagnostic logs.

## F. Language and Europe-first release — confirmed requirements
- Agree initial European countries and a complete supported-language matrix; include English. Do not invent approval for German or other locales.
- Require a supported-language choice before onboarding/legal acceptance. A device-language suggestion does not replace user choice. Provide later switching and remember the preference.
- Localize the entire shipped app: world labels, explanations, interaction feedback, accessibility text, authentication, settings, legal pages, errors, and any audio/notifications.
- Test each supported locale through account creation/login, AGB decisions, exploration, switching, restart, and account recovery. Verify text expansion and locale formatting.
- Missing supported-locale translations block release. Define fallback for unsupported languages and cross-device preference behavior.

## G. Release decision
Maintain gate, revision, device/locale, evidence, result, and outstanding issues. Owner confirms product/market scope and public release. Store publication, signing, purchases, external services, and production credentials are outside the autonomous development loop. Monetization is a separate decision; if introduced, add its flow-specific criteria before release.

## H. Appearance — confirmed requirement
- Two complete schemes, Bright and Dark, cover all shipped surfaces and interaction states, including the explorable environment and system bars.
- First use defaults to System. While System is selected, a device appearance change updates the app without restarting it or interrupting the current interaction.
- Settings exposes Design with System, Bright, and Dark choices. Explicit Bright/Dark overrides ignore device-theme changes; returning to System applies the current device appearance immediately.
- Persist the preference across app restarts. Changing appearance preserves navigation and interaction state.
- No information box, popup, toast, or onboarding message accompanies automatic appearance changes.
- Verify contrast, legibility, selected/disabled states, and system-bar icons in both schemes. Localize the setting and its choices; expose the selected choice accessibly.
- Test the System/Bright/Dark preference against both device modes, live system changes, overrides, return to System, and relaunch. Capture fresh evidence for both schemes.
