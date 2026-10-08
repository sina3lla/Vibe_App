"""Milestone definitions for the bounded autonomous build sequence.

Each Milestone is a controller-owned acceptance-criteria source. loop.py writes
its `brief` into agent/CURRENT_TASK.md at the start of that milestone's cycle;
the Claude subprocess cannot edit agent/** (see settings deny-list in loop.py),
so it cannot rewrite its own acceptance criteria mid-cycle.

Mapping to docs/BUILD_PLAN.md's six numbered milestones: CORE below already
combines BUILD_PLAN items 1 and 2 (explorable shell/territories plus
settings/appearance/language/persistence), because agent/CURRENT_TASK.md had
already scoped those together before this sequencer existed, and splitting an
owner-tuned bounded task retroactively risked silently changing its scope.
ACCOUNT = BUILD_PLAN item 3, LOCALIZATION = item 4, QA = item 5,
RELEASE = item 6.

`required_env`: environment variables that must be set before this milestone
starts. Missing ones block only this milestone (see loop.py execute()); other
milestones that do not depend on it continue.

`visual_key`, `themes`, `languages`: passed to agent/visual_qa.py so each
milestone gets checks appropriate to what it actually changed, instead of the
old fixed Vibrant/Mannequin/Ascension journey.

`controller_only`: True means loop.py does not ask Claude to implement new
scope for this milestone (there should be none left); it still runs gates and
one Codex sanity review, and will still invoke Claude to fix a real defect if
Codex finds one.
"""
from dataclasses import dataclass

COMPLETION_FOOTER = """
## Completion
All app code for this milestone, not just a plan or mockup. Orchestrator runs checks; do not attempt shell tools. Report files changed, design decisions, and limits honestly. You may edit only app/src/main, app/src/test, app/src/androidTest. Do not edit scripts/docs/build files. The supervising agent continues the full build after this milestone; do not claim launch readiness.

## Execution owner
The owner started this automated loop from Android Studio. Your current role is bounded implementation of this one milestone; do not launch other agents, loops, or milestones. The controller advances automatically once this milestone's checks and review pass; it never publishes, pushes, deploys, or spends on services on its own.
"""

ENGINE_DESIGN_BRIEF = """# Current Task — evaluate an Android 3D approach (design phase, read-only)

The owner has confirmed the new creative direction: an original, magical, explorable 3D world with surreal environments and playful, discovery-driven interaction. Froopyland (Rick and Morty) is a conceptual tone reference only — strange, shifting, inventive — never a source of artwork, characters, or environments to copy or imitate. There is no reflection flow, journaling prompt, emotional debrief, chatbot, or educational video; understanding still has to emerge through interaction, with optional brief explanations in context, exactly as before.

You cannot write files in this phase. Read CLAUDE.md, docs/PRODUCT_VISION.md, docs/WORLD_DESIGN.md, docs/LAUNCH_CRITERIA.md, app/build.gradle.kts, gradle/libs.versions.toml, and agent/visual_qa.py (to understand how the controller taps controls by Compose testTag today).

## Evaluate
Recommend exactly one Android 3D rendering approach for this project and the specific dependency coordinates/version you would add. Weigh, at minimum:
- **Performance**: frame-time budget on a mid-range device; thermal/battery cost of a persistent 3D scene versus a mostly-static one with occasional animated accents.
- **Accessibility**: a raw GL/Filament surface is not itself accessible to TalkBack or to the controller's resource-id-based tap automation — interactive controls must stay as real Compose composables overlaid on the 3D view (or expose equivalent invisible semantics nodes at the same screen position), and a non-spatial/reduced-motion fallback must remain possible without losing the core interaction.
- **Asset licensing**: original or properly licensed low-poly/procedural assets only; flag any approach that would tempt importing unlicensed third-party models, and note the APK-size cost of any embedded assets.
- **Automated verification**: whether the controller's adb/uiautomator screenshot-and-tap journey (agent/visual_qa.py) can still drive it — this must not require a new, separate verification mechanism.
- **Version evidence**: you have no network access in this phase, so you cannot personally check Maven metadata. Read docs/decisions/3D_ENGINE_EVALUATION.md first — if it already records a version for your recommended library that was verified against Maven metadata (not just named from memory), use that exact version and cite it. If it does not, state plainly in your recommendation that the exact version still needs to be verified against official Maven metadata before anyone implements against it, and do not supply one from memory — a prior cycle (agent/runs/20261008-223002) guessed an unverified patch version that turned out not to exist, and the resulting repair attempt then tried to search outside the repository for it, which was correctly denied. Never recommend a dynamic/wildcard version constraint (e.g. "1.+", "latest.release") as a substitute for verification.
- **Integration cost, and what "minimal" actually has to cover**: the result must be an actual visible 3D object (real geometry, not just an ambient color/skybox with nothing in it) — a flat-colored background proves the surface mounts in Compose but does not prove anything about rendering a shape, and is not an acceptable final state for this milestone. One engine library dependency plus its version-catalog entry is the normal ceiling; a second, small, clearly-related runtime dependency from the *same* engine family (e.g. a runtime material/shader compiler that the engine needs specifically to display geometry, not a second competing engine) is acceptable if you name upfront why the first dependency alone cannot render a visible object. Do not recommend an approach needing a build-time Gradle plugin, a native build system (CMake/NDK), a second IDE toolchain, or a settings.gradle.kts change — if every approach you can find needs one of those to get past a flat/empty scene, say so plainly and recommend the smallest concrete next-milestone ask (e.g. "approve the Filament Gradle plugin as its own scoped milestone") instead of quietly recommending an engine that can only ever produce a skybox.

State your single recommendation plainly, the exact Gradle coordinate(s)/version (naming both dependencies if two are needed and why), and the main trade-off you accepted. This is a working recommendation for the next bounded milestone to implement, not an owner-approved architecture decision — say so if your confidence is limited by not having run anything on real hardware.
"""

ENGINE_BRIEF = """# Current Task — add the selected 3D rendering dependency and a minimal harness

Read docs/decisions/3D_ENGINE_EVALUATION.md (just written by the controller from the prior design-phase response) and docs/PRODUCT_VISION.md/docs/WORLD_DESIGN.md for the magical-surreal creative direction. Froopyland is a tone reference only, never a copied asset/character source.

## Build now
Add the recommended dependency (or dependencies — up to two small, clearly related ones, e.g. an engine library plus the runtime material/shader compiler it specifically needs to render geometry, if the design-phase recommendation named that need) to app/build.gradle.kts and, if it uses the version catalog, to gradle/libs.versions.toml. These are the only two files outside app/src/main, app/src/test, and app/src/androidTest you may touch this milestone — no other Gradle file, no wrapper, no settings.gradle.kts, no Gradle plugin application.

**Every version you write must be an exact pin you can point to evidence for** — never a dynamic/wildcard constraint ("1.+", "latest.release", "latest.integration"; the controller now fails the build fast if it finds one, before even running Gradle). You have no network access, so "evidence" means: docs/decisions/3D_ENGINE_EVALUATION.md already records a version verified against Maven metadata (use that exact one), or the version was already present and working before this milestone touched it. If neither is true and you cannot otherwise confirm a version is real from inside the repository, do not guess one and do not try to search, fetch, or read anything outside this repository to find out (it will be denied, and that denial itself does not advance the task) — state exactly what needs external verification (the group/artifact id and what kind of confirmation is needed) in your completion report and stop there for that dependency.

Build a minimal 3D scene harness proving the pipeline renders inside the existing Compose shell, and render an actual visible object — real geometry (your own simple low-poly shape: a cube, sphere, or similarly simple primitive is enough), not only an ambient color field or skybox with nothing in it. A flat-colored background alone does not satisfy this milestone, even if the surface technically mounts. House it in ordinary Compose UI (not raw GL) carrying any interactive controls. Respect reduce-motion: provide an idle state with no required continuous animation, and a text/non-spatial fallback that does not depend on the 3D surface rendering at all. No territory content, no chatbot, no journaling or reflection flow — this milestone only proves the engine choice is viable, renders something real, and is automatable.

If, while implementing, you discover the chosen approach genuinely cannot render a visible object within the file/dependency boundary above (for example, it turns out to need a build-time Gradle plugin after all) — do not silently fall back to an empty scene and call it done. Render the best non-plugin substitute you can that is still visibly an object (not just a color), state the exact blocker in your completion report, and name the smallest concrete follow-up request (e.g. "approve the Filament Gradle plugin as its own scoped milestone") for the controller to raise with the owner.

Expose a stable Compose test tag `engine-canvas` on the harness's own screen (or on whatever existing screen hosts it) via semantics testTagsAsResourceId, so agent/visual_qa.py's `engine` journey can find and screenshot it. If no interactive control is needed yet, a visible placeholder scene with that tag is sufficient evidence.

Add a minimal JVM or instrumentation test asserting the harness composable does not crash on first composition and that its non-spatial fallback is reachable without the 3D surface.
"""

CORE_BRIEF = """# Current Task — build the complete explorable app core

Owner authorized the FULL BUILD, not a prototype-only stop. This milestone implements the complete offline product while provider/language decisions are obtained. Read docs/BUILD_PLAN.md, PRODUCT_VISION, WORLD_DESIGN, CREATIVE_PROCESS, and LAUNCH_CRITERIA, and docs/decisions/3D_ENGINE_EVALUATION.md for the chosen rendering approach from the prior engine milestone.

## Build now
Replace the old three-ritual home with an original, magical, explorable world: surreal environments, playful interaction, and discovery, built on the 3D (or hybrid 3D/Compose) approach the engine milestone already wired in. Froopyland is a conceptual tone reference only — never a source of artwork, characters, or environments to copy. No hidden prototype entry. Create five territories: Attention (competing signals / urgency versus importance), Wants & Needs (desire/obligation/uncertainty as hypotheses), Boundaries (distance and permission), Perspective (observation/interpretation/response), Rest & Ambition (capacity and chosen pace). At least two meaningful independently usable interactions per territory, with clear feedback and optional short explanations. Interactions must differ substantively, not five copies of the same slider. No forced sequence, quizzes, guaranteed benefit, or mandatory emotional disclosure; no reflection flow, journaling prompt, chatbot, or emotional debrief. Learn by changing/comparing models, with visible limits.

Design a visually coherent environment with a distinctive spatial map and tactile interactive scenes. Keep accessible text navigation as an alternative, and keep every interactive control a real Compose composable (or an equivalent accessible semantics node) even where it sits over a 3D view — the controller's screenshot/tap automation and TalkBack both depend on this. No chatbot, videos, additional engine or dependency changes beyond what the engine milestone already added, web services, or fabricated therapy efficacy; original or properly licensed assets only. Keep old unused source only if needed to avoid unrelated work; remove camera permission if no reachable feature needs it.

Required app functionality: first-run language selection; English and German, now explicitly confirmed by the owner; all NEW strings localized consistently via Android resources; live System/Bright/Dark appearance, default System, persisted preference, no notifications; reduce-motion/quiet setting; local saved discoveries with explicit remove and confirmed erase-all; a world map, discoveries, and settings navigation; back and activity restoration; system-bar contrast and safe insets; offline operation. Persist non-sensitive interaction choices and bookmarks. No freeform personal journal or analytics.

This milestone does not implement account/login; a later dedicated milestone integrates the existing FeelY backend. Do not add a placeholder fake-login screen beyond a truthful "not connected yet" state if a settings/account entry point is natural here; do not collect passwords without a backend.

Add meaningful JVM tests for any pure model rules and Compose instrumentation tests for first-run language, independent territories, settings persistence, navigation/recreation, and saved discoveries/removal. Existing navigation test must be updated for the new real home; do not simply delete regression coverage. Expose stable Compose test tags via semantics testTagsAsResourceId for controller screenshot navigation: world-map, territory-attention, territory-needs, territory-boundaries, territory-perspective, territory-rest, nav-world, nav-discoveries, nav-settings, language-en, language-de, design-system, design-bright, design-dark, quiet-toggle, back. Each territory's two (or more) required interactions must additionally expose `interaction-<territory>-1`, `interaction-<territory>-2`, … (e.g. `interaction-attention-1`) on whichever control actually performs that interaction, so the controller's visual QA can exercise them, not just enter and leave the territory.
"""

ACCOUNT_BRIEF = """# Current Task — FeelY account and terms integration

Read docs/AUTH_INTEGRATION.md in full before writing code; it is the confirmed contract for the existing FeelY backend. Do not build a separate fake account system and do not invent a successful login.

## Build now
The controller has generated app/src/main/java/com/example/eso1/data/auth/ApiConfig.kt (or the equivalent package you find) from the FEELY_API_BASE environment value confirmed by the owner (https://api.feel-y.com/api/v1). Read that generated file and use its constant as the single source of the API base; do not hard-code a second copy of the host, and do not infer the host from the GitHub repository URL. Treat the base as unverified-live even though it is owner-confirmed: a prior live check returned HTTP 403 / error 1010, so implement genuine network-error and unexpected-response states rather than assuming the deployment is reachable from this environment.

Implement login, registration (respecting /auth/captcha/config when enabled — do not bypass or disable verification to make automation pass), email verification request/confirm, and password-reset request/confirm against the documented routes. Wire Google login only if /auth/google/config reports it enabled, and treat that alone as insufficient proof of Android client compatibility; if you cannot verify an Android OAuth client is registered, leave it visibly unavailable rather than wiring a credential flow that will fail silently. Store tokens with an appropriate platform-backed mechanism; never log tokens, passwords, or full error response bodies. Respect rate limits (429/503) instead of retrying indefinitely. Implement real loading/success/error/cancel/sign-out/expired-session states — no screen may present a pretend-authenticated state.

Terms acceptance: no versioned AGB-acceptance endpoint was found in the inspected FeelY auth routes/schemas. Owner-reported findings about a newer `terms_acceptances` store, and about access-enforcement and presented-language recording remaining gaps there, could not be independently reverified in this preparation session (no authenticated repository access was available). Treat those as unverified reports, not confirmed facts. Implement an explicit, unselected-by-default, full-text acceptance step before authenticated access, record account/version/timestamp/presented-language locally, and send that record to the backend only through an endpoint you can confirm exists in the inspected contract; if none exists, say so plainly in your completion report instead of fabricating a field the server will silently ignore. Keep draft legal copy clearly labeled draft and distinct from privacy information.

Localize all new user-facing outcomes into English and German, mapping known server error strings to localized messages without logging sensitive response contents.

Add stable Compose test tags for controller screenshot navigation: nav-account, auth-email, auth-password, auth-submit, auth-signout, terms-accept. Add JVM/instrumentation tests for client-side validation, token storage/sign-out, and the terms-acceptance gate (including that a declined acceptance does not grant access).

## Prerequisite note
If FEELY_API_BASE was not provided, the controller will not start this milestone at all; you will only see this brief when that value is present. Its presence confirms the owner's chosen base URL, not that the deployment is live, that email delivery works, or that Google Android credentials are configured — verify what you can from the documented contract and flag the rest as outstanding in your completion report.
"""

LOCALIZATION_BRIEF = """# Current Task — complete localization and content sourcing

## Build now
Complete German and English string coverage for every screen implemented so far (territories, settings, and account/terms screens if that milestone has already produced strings — check before assuming they exist). Do not translate or polish screens that were never built; if the account milestone was blocked, say so rather than inventing copy for a flow that doesn't exist yet.

Review the explanatory copy already written for each territory against WORLD_DESIGN.md's content-record requirement: intended distinction, source/status of factual claims, limits of the metaphor. Do not invent citations. Where a factual claim about bodily or psychological mechanisms lacks a documented source, leave the copy but state plainly in your completion report which strings still need content review before release — this report text is preserved in the run log for the owner, since you cannot edit docs/ yourself.

Verify text expansion and basic locale formatting (no truncated/overlapping German strings at default and 200% font scale on the screens you can reach). Do not add a third locale; the owner has confirmed only English and German.

Add or extend instrumentation tests that assert both locales render the territory list, settings, and (if present) account screens without missing-resource fallbacks.
"""

QA_BRIEF = """# Current Task — comprehensive build, test, and device QA

## Build now
No new product scope. Run through the app as implemented so far (territories, settings/appearance/language, and account/terms if that milestone passed) and fix any real defect the controller's gates or Codex review surfaces: build/test/lint failures, broken navigation/back/restoration, inaccessible controls, theme or locale regressions, or a saved-discoveries/data-lifecycle bug (process recreation, backgrounding, erase-all). Do not add features or expand the territory list.

If accessibility (TalkBack order/labels, large text, reduced motion, non-spatial alternative to spatial gestures) has a reachable, fixable gap in existing screens, fix it. Do not claim coverage you have not actually exercised.

This milestone's evidence must include both themes and both languages across whatever screens exist; the controller's visual QA is configured accordingly. Missing evidence blocks PASS regardless of how the code looks.
"""

RELEASE_BRIEF = """# Current Task — debug APK and honest launch checklist

## Build now
No new implementation is expected here. The controller runs the full build/test/lint/connected-test/visual-QA gate one more time and assembles a launch checklist from docs/LAUNCH_CRITERIA.md against the actual recorded milestone outcomes (passed, blocked, or not verified) — it does not ask you to write that checklist, and you must not write your own summary of launch readiness into app code or claim the product is release-ready.

If this milestone's Codex review surfaces a real, in-scope defect, fix only that defect within app/src/main, app/src/test, app/src/androidTest. Otherwise make no changes.
"""

MILESTONE_ORDER = ("engine", "core", "account", "localization", "qa", "release")


@dataclass(frozen=True)
class Milestone:
    key: str
    title: str
    brief: str
    required_env: tuple = ()
    visual_key: str = "core"
    themes: tuple = ("system",)
    languages: tuple = ("en",)
    controller_only: bool = False
    # Optional read-only research/decision phase run before `brief`; its response text is
    # captured verbatim by the controller into docs/decisions/3D_ENGINE_EVALUATION.md.
    design_brief: str = None
    # Exact file paths (not globs) this milestone's implement/fix calls may additionally
    # write beyond app/src/**, e.g. the one Gradle file needed to add a dependency.
    extra_paths: tuple = ()

    def full_brief(self):
        footer = COMPLETION_FOOTER
        if self.extra_paths:
            allowed = "app/src/main, app/src/test, app/src/androidTest, and exactly " + ", ".join(self.extra_paths)
            footer = footer.replace(
                "You may edit only app/src/main, app/src/test, app/src/androidTest. Do not edit scripts/docs/build files.",
                f"You may edit only {allowed} — no other script, doc, or build file.",
            )
        return self.brief.rstrip() + "\n" + footer


MILESTONES = [
    Milestone(
        key="engine",
        title="Evaluate and wire up an Android 3D rendering approach",
        brief=ENGINE_BRIEF,
        design_brief=ENGINE_DESIGN_BRIEF,
        required_env=(),
        visual_key="engine",
        themes=("system",),
        languages=("en",),
        extra_paths=("app/build.gradle.kts", "gradle/libs.versions.toml"),
    ),
    Milestone(
        key="core",
        title="Explorable core, territories, settings, persistence",
        brief=CORE_BRIEF,
        required_env=(),
        visual_key="core",
        themes=("system", "bright", "dark"),
        languages=("en", "de"),
    ),
    Milestone(
        key="account",
        title="FeelY account and terms integration",
        brief=ACCOUNT_BRIEF,
        required_env=("FEELY_API_BASE",),
        visual_key="account",
        themes=("system",),
        languages=("en", "de"),
    ),
    Milestone(
        key="localization",
        title="Complete localization and content sourcing",
        brief=LOCALIZATION_BRIEF,
        required_env=(),
        visual_key="localization",
        themes=("system",),
        languages=("en", "de"),
    ),
    Milestone(
        key="qa",
        title="Comprehensive build, test, and device QA",
        brief=QA_BRIEF,
        required_env=(),
        visual_key="qa",
        themes=("system", "bright", "dark"),
        languages=("en", "de"),
    ),
    Milestone(
        key="release",
        title="Debug APK and honest launch checklist",
        brief=RELEASE_BRIEF,
        required_env=(),
        visual_key="qa",
        themes=("system", "bright", "dark"),
        languages=("en", "de"),
        controller_only=True,
    ),
]

MILESTONES_BY_KEY = {m.key: m for m in MILESTONES}

assert tuple(m.key for m in MILESTONES) == MILESTONE_ORDER
