# Current Task — Preserve navigation on recreation

Improve one bounded reliability issue: the selected experience currently resets to Home when Android recreates the activity.

## Acceptance criteria
- Preserve the selected destination through activity recreation using saveable state.
- Home and system Back still behave predictably for all three experiences.
- Add a meaningful Android Compose regression test proving destination survives state restoration, without requiring camera permission or playing audio.
- Do not persist active audio playback or claim to restore every ritual's internal state in this task.
- Build, unit tests, lint, and the emulator smoke journey pass. The orchestrator also runs connected Android tests for this task.
- Keep the current visual design and branding; no unrelated refactors.

This deliberately small first task validates the real implementation/review/handoff loop. A PASS does not satisfy all launch gates.

## Scope after product clarification
This remains an infrastructure trial on the existing prototype, not endorsement of its ritual content. Do not implement or invent a somatic practice in this task. The guided recommendation journey and sourced practice library are a subsequent design task.
