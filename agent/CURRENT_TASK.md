# Proposed Task — first playable encounter

Status: concept approved for a reversible prototype. Before execution, complete the controller/QA prerequisites in docs/IMPLEMENTATION_BRIEF.md. Appearance requirements are approved. No loop is started by saving this task.

## Outcome
Create a small explorable Android space where a person can discover a distinction between competing demands for attention and their own choice of focus. Make it useful to someone experiencing mental crowding without claiming to treat panic.

## Creative brief
Use the competing-signals concept in WORLD_DESIGN as a starting hypothesis. Choose the actual metaphor, composition, interaction, and wording. Build one coherent interpretation, not a menu of variants. The user must be able to explore in different orders, linger, and leave. Do not require a chatbot, video, intake questionnaire, or prescribed session sequence.

Target a contained implementation using the existing Android stack. Do not introduce a game engine, backend, account integration, or new dependencies in this slice. Login/AGB/localization remain release obligations; keep display strings externalized for later translation. Preserve existing routes and unrelated uncommitted work until a separate task authorizes replacement. Place the slice behind a clear local prototype entry.

## Acceptance criteria
- An understandable entry leads into a coherent small environment with at least two independently reachable interactions; visiting one never requires completing the other.
- Each interaction helps illustrate a concrete distinction. At least one allows comparison between two choices with a comprehensible model response.
- Brief optional explanatory text appears in context, can be dismissed, and does not claim to measure or change the user's internal state.
- A persistent exit, a quieter/reduced-motion presentation, and accessible non-drag controls work. Core functionality does not depend on audio.
- The first frame does not manufacture overload. No flashing, alarms, countdowns, distress scores, required emotional reports, or simulated therapeutic success.
- Leaving and returning, Back, and activity recreation preserve or reset state intentionally. Add meaningful regression coverage for navigation and chosen-state behavior.
- Relevant debug build, unit tests, lint, connected tests, and the updated emulator journey pass. Fresh evidence shows initial entry, both interactions, explanation open/dismissed, quiet mode, exit, and return.

## Handoff
Explain the design hypothesis and what the visitor can learn. Provide evidence references, remaining limitations, and up to three useful questions for owner feedback. Do not treat absent taste feedback as rejection or approval. Do not start a second territory automatically.

## Definition of done
A playable candidate ready to react to. It need not be the final aesthetic, full world, clinically validated intervention, or sellable release. Task PASS confirms this slice only.

## Appearance requirement added before implementation
Include both Bright and Dark schemes in this first playable slice. Follow the phone's appearance silently by default, with Settings → Design → System, Bright, Dark. Persist the choice; explicit overrides take precedence over device changes. Apply live changes without losing the visitor's place or interaction state. Do not add an information box or automatic-change notification.

Add meaningful checks for default system behavior, manual override, persistence, and return to System. Include screenshots of the playable space in both schemes and of the selected settings control. Extend the emulator journey to exercise appearance changes before treating this slice as verified.
