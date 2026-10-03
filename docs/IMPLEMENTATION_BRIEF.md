# FeelY companion — explorable world draft

Status: adopted for a reversible prototype on 2026-10-03. Includes approved System/Bright/Dark appearance behavior.

## The pitch
Build a place people can explore while something is happening inside them. They discover useful distinctions through interaction, receive short explanations in context, and remain free to decide what fits their experience. The product earns its value through the quality of those interactions and explanations.

The central creative test: **Does interacting here help someone understand the moment they are still inside?**

## Read the pack
1. docs/PRODUCT_VISION.md — the enduring purpose and current product direction.
2. docs/WORLD_DESIGN.md — a design grammar plus provisional examples, not a prescribed aesthetic.
3. docs/CREATIVE_PROCESS.md — how evolving ideas become bounded, reviewable work.
4. docs/LAUNCH_CRITERIA.md — prototype checks separated from release obligations.
5. CLAUDE.md and AGENTS.md — implementation freedom and independent review.
6. agent/CURRENT_TASK.md — the proposed first playable slice.

## Existing work and activation
These files supersede the earlier guided-practice direction. Historical briefs are in docs/archive/pre-explorable-world and are not active requirements. The outdated FeelY design files are not dependencies.

The navigation-test compilation failure is corrected and the navigation change is included in this checkpoint. Before executing the proposed task, run the connected device test and validate the original bounded agent cycle. The existing screenshot runner assumes Vibrant/Mannequin/Ascension; update its journey for the new slice before treating it as valid evidence. This requires a separate infrastructure task because ordinary implementation cycles cannot edit agent scripts.

The active files are installed at their stated repository paths. Historical copies are retained only for context; current instructions take precedence.

## Open decisions that do not block prototyping
Final name, visual style, 2D versus 3D, navigation metaphor, initial world size, payment model, authentication provider, launch countries and languages beyond English. Agents may propose reversible prototype choices without treating them as approved release decisions.

The owner authorized the reversible prototype and a Git backup. Purchases, service provisioning, and publishing remain outside that authorization.

## Backup verification — 2026-10-03
Debug build, unit tests, lint, Android-test APK compilation, and seven controller tests passed. No emulator was attached, so the connected device test and full autonomous cycle remain unverified. Bright/Dark/System is specified in the brief; the new world and theme selector are not yet implemented.

## Full-build authorization
The owner now requests the complete app. docs/BUILD_PLAN.md defines the implementation sequence. Continue across milestones; the former single-slice-only stop is superseded. Tests, permission boundaries, and release-only approvals remain in force.
