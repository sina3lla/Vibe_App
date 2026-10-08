# Autonomous development loop

The loop is currently **stopped** (`agent/STOP` is present) and the owner has not authorized starting it. This file documents the exact commands for when they do.

## Start

From a clean, committed `agent/autonomous-dev` branch, with the emulator already running:

```sh
rm agent/STOP   # only once the owner has decided to start
python3 agent/loop.py --serial emulator-5554
```

The `account` milestone additionally requires the API base to be supplied explicitly (the controller will not guess it or fabricate a working deployment):

```sh
export FEELY_API_BASE=https://api.feel-y.com/api/v1
```

Without it, `account` is marked `blocked` and skipped; `engine`, `core`, `localization`, `qa`, and `release` still proceed (see **Milestones and blocking** below).

## Stop

```sh
touch agent/STOP
```

or Ctrl-C the running process. The controller checks the stop file every second during child processes and terminates their process group. It commits a local-only WIP checkpoint of whatever the in-progress milestone had already produced before exiting (see **Checkpoints and resume**) — it does not discard work. Remove `agent/STOP` deliberately before the next start.

## Resume

Run the exact same start command again:

```sh
python3 agent/loop.py --serial emulator-5554
```

The controller reads `agent/runs/milestones-state.json` (gitignored, local only) and skips any milestone already marked `passed`, retries one marked `blocked` if its required environment variable is now set, and re-enters one marked `in_progress` from a WIP checkpoint. To discard saved progress and run the whole sequence again from `engine` (this does **not** discard already-committed app code, only the resume pointer):

```sh
python3 agent/loop.py --serial emulator-5554 --restart
```

## What you will see while it runs

The agents run **headlessly** — Claude and Codex are CLI subprocesses with no window of their own; everything you see comes from this controller's own terminal output, its log files, and the emulator's screen (which only changes after a build/install step actually runs, not while Claude or Codex are "thinking").

In the terminal that started the loop, expect:
- One `START <label> — <milestone> · <actor> · <action> (timeout <n>s)` line when each step begins (`<actor>` is `Claude`, `automated checks` [Gradle/visual QA], or `Codex`).
- A heartbeat line **at least every 30 seconds** during a long step: elapsed time, time left until that step's own timeout, and either a short redacted summary of new subprocess output or the honest `process still running; no new output to show yet` — never a fabricated percentage, and elapsed time alone is never presented as evidence of progress.
- One `DONE <label> (<n>s)` line when the step finishes, or a specific failure reason (e.g. which exact permission was denied, or the last matching `FAILED`/`error:` line from the log) instead of a bare "failed; see log" pointer.
- A final plain-language summary on exit — why it stopped, what was saved (a WIP checkpoint commit, if any), what remains unverified, and the exact command to resume — whether it exited cleanly, hit the STOP file/timeout, was interrupted with Ctrl-C, or hit a genuine error.

**To follow along from a second terminal**, tail the current run's log and the live status file:

```sh
tail -f agent/runs/STATUS.md
tail -f "agent/runs/$(ls -t agent/runs | grep -E '^[0-9]{8}-[0-9]{6}$' | head -1)/RUN_LOG.md"
```

`agent/runs/STATUS.md` (controller-owned, gitignored, rewritten throughout the run — never hand-edit it) always shows: the run ID and when it was last updated; whether the run is running/stopped/failed/complete; the current milestone, actor, and action; which milestones are completed vs. remaining; the latest Codex-verified result with links to its evidence; the current blocker, if any; whether you need to do anything and the exact next step; and the latest checkpoint commit with whether it's been pushed. A recent timestamp in STATUS.md is **not** proof the process is still alive on its own — if you want to be sure, check for the process itself (`pgrep -fl agent/loop.py`) rather than trusting the file alone; an abrupt kill (e.g. `kill -9`, a machine sleep/crash) can leave it stale.

**When does the emulator actually change?** Only after a milestone's `implement`/`buildfix`/`fix` Claude call finishes and the controller's own `gates()` step runs — that's when `gradlew assembleDebug`/`test`/`lintDebug`/`connectedDebugAndroidTest` execute and `agent/visual_qa.py` installs the freshly built APK and drives it. During the Claude or Codex steps themselves (often the longest part of a cycle), the emulator will sit on whatever it was last showing — that is expected, not a hang.

## What it does

`agent/milestones.py` defines six bounded milestones, run in order, each its own implement → gates → Codex review → fix cycle:

1. **engine** — a read-only design phase recommends an Android 3D rendering approach (performance/accessibility/licensing/automated-verification trade-offs, and now explicitly required to actually render a visible object, not just an ambient color/skybox), which the controller captures into `docs/decisions/3D_ENGINE_EVALUATION.md` (overwritten each design phase); a second phase adds that dependency — and, if genuinely needed to render real geometry (not a second competing engine), one small related dependency such as a runtime material compiler — to `app/build.gradle.kts`/`gradle/libs.versions.toml` (the only milestone with write access to any Gradle file) plus a minimal 3D harness. Verified dependency evidence that must survive across runs (exact versions, required initialization, integration code) lives in `docs/reference/` instead — those files are never overwritten by the controller. Acceptance requires *native*-rendered geometry specifically: a Compose `Canvas` drawing standing in for it, or a "native pipeline unavailable" screen, is a legitimate accessibility fallback but not a pass — `agent/visual_qa.py` mechanically checks an `engine-render-status` tag reads exactly `"native"` (not just that something is visible) before this milestone's gate can succeed, and Codex's review for this milestone is given an extra instruction to check that distinction explicitly (`Milestone.review_focus`), after one cycle shipped a 2D substitute and an overclaiming completion report that Codex correctly caught and BLOCKED on.
2. **core** — the explorable shell, five territories, settings/appearance/language, persistence (combines docs/BUILD_PLAN.md items 1–2; see the comment at the top of agent/milestones.py for why).
3. **account** — FeelY backend integration per docs/AUTH_INTEGRATION.md. Blocked without `FEELY_API_BASE`.
4. **localization** — completes German/English coverage and flags content-sourcing gaps for whatever was actually built.
5. **qa** — comprehensive build/test/lint/device-test/visual pass across both themes and both languages; fixes real defects only, no new scope.
6. **release** — re-runs the full gate, then the controller (not Claude) writes `agent/runs/<run>/LAUNCH_CHECKLIST.md` from the recorded milestone outcomes. This is a status snapshot, never a release decision or a claim of launch readiness.

A milestone's acceptance criteria are controller-owned: `agent/CURRENT_TASK.md` is regenerated by the controller from `agent/milestones.py` at the start of each milestone, and the Claude subprocess is denied `Edit`/`Write` on `agent/**`, so it cannot rewrite its own task description mid-cycle.

## Milestones and blocking

A milestone whose `required_env` is unset is marked `blocked: missing env: <VAR>` in the state file and skipped; milestones that don't depend on it still run (today, only `account` has a required env var). A milestone that genuinely fails — exhausts its build-repair or review-retry budget, or hits a scope violation — stops the **whole run** with a nonzero exit status; later milestones are not attempted on top of a failed one. Missing evidence (no screenshots, a malformed Codex response) is always treated as a failure, never as a pass.

## Checkpoints and resume

A milestone **PASS** triggers one local-only `git commit` (never a push) of exactly the files that milestone was allowed to touch — explicitly staged, never `git add -A`; credentials (`.env*`, `local.properties`, `*.jks`, `*.keystore`) and run artifacts (`agent/runs/**`, already gitignored) are excluded even if somehow modified. The commit happens *before* the milestone is recorded as `passed`: if the commit itself fails for any reason, the state file is not updated, so a resumed run retries the milestone instead of silently skipping it over an uncommitted tree.

Scope checking and checkpoint staging are tracked separately on purpose: a controller-written file (`agent/CURRENT_TASK.md`, the engine milestone's `docs/decisions/3D_ENGINE_EVALUATION.md`, the account milestone's generated `ApiConfig.kt`) is never mistaken for a Claude edit by the scope check, but it is still correctly included in what gets committed — the two checks used to share one tracking dict, which could make a controller-written file quietly never get committed at all.

If the run stops mid-milestone (STOP file, timeout, or an unhandled error that isn't a scope violation), the controller makes the same kind of commit labeled as a WIP checkpoint and marks that milestone `in_progress` in the state file, so nothing is left uncommitted and undiscoverable. A scope violation (Claude touched a forbidden path, or git HEAD changed unexpectedly) is the one case left **uncommitted** on purpose, so a human inspects it before anything is folded into history. The `engine` milestone's own grant to touch `app/build.gradle.kts`/`gradle/libs.versions.toml` is honored consistently across its implement call, its Codex review, and its read-only completion handoff — a legitimate dependency change made earlier in the milestone does not get flagged as a violation later in the same milestone's cycle.

**2026-10-08 permission-pattern fix**: the first real engine-milestone run was denied editing `app/build.gradle.kts` even though it was granted that exact path. The cause: Claude Code's permission deny patterns match gitignore-style — a bare filename with no `/` in it (like the deny rule meant only for the *root* `build.gradle.kts`) matches that filename at *any* depth, so it was also denying the nested `app/build.gradle.kts`. `build_deny_list()` now root-anchors every bare top-level filename (`/build.gradle.kts`, `/settings.gradle.kts`, `/gradle.properties`, `/gradlew*`, `/AGENTS.md`, `/CLAUDE.md`) so they no longer shadow a same-named file elsewhere in the tree; patterns that already contain a `/` (e.g. `app/build.gradle.kts`, `gradle/libs.versions.toml`) were already root-relative and are unchanged. See `agent/tests/test_loop.py`'s `PermissionDenyListTests`.

## Limits

- `--max-reviews` (default 3): Codex review rounds per milestone.
- `--max-build-repairs` (default 2): build/test/lint/visual-QA repair attempts per milestone, counted separately from review rounds.
- `--minutes` (default 180): overall runtime for *this invocation*; hitting it stops cleanly (WIP checkpoint) and the next invocation resumes.
- `--claude-budget` (default $3, max $10): per-Claude-invocation USD cap, not a combined cap. Codex uses the authenticated account with no monetary cap here.

Per milestone, the worst case is 1 implement + `max-build-repairs` build-fix calls + (`max-reviews` − 1) review-fix calls + 1 handoff = up to 6 Claude calls and up to 3 Codex calls at the defaults. Across all six milestones that's a worst-case ceiling of 36 Claude calls (≈$108 at the default per-call cap) and 18 Codex calls for one fully-exhausted run — realistically far less, since most milestones should pass well before exhausting retries.

Requires Python 3, Git, current Claude with `--restricted`/`--safe-mode`, Codex with `--ignore-user-config`, Android SDK/adb, Java, and a running emulator. The local default SDK and Android Studio Java paths support this Mac. Override `JAVA_HOME` or `ANDROID_HOME` when necessary. Authenticate both CLIs interactively before running. Never put credentials in this repo.

Claude receives only Read/Glob/Grep/Edit/Write, restricted to its workspace, with hooks/customizations and MCP disabled. It cannot invoke a shell. Codex runs read-only with approvals disabled. The controller rejects changes outside the current milestone's allowed paths before executing Gradle — for every milestone except `engine` that's `app/src/main`, `app/src/test`, `app/src/androidTest`; `engine` additionally allows exactly `app/build.gradle.kts` and `gradle/libs.versions.toml`, never the wrapper, `settings.gradle.kts`, or the root build file. This is a local development boundary, not a hostile-code container: Gradle and instrumentation execute app code on your machine/emulator. Use a disposable environment before applying this to untrusted projects. The controller never changes permissions to get around failure.

## Evidence

Logs, reviews, screenshots, UI trees, and manifests live under ignored `agent/runs/<timestamp>/`, including `LAUNCH_CHECKLIST.md` written at the end of the `release` milestone. See each run's `RUN_LOG.md`. `agent/REVIEW.md` is historical context only; current reviews are uniquely named within the run. No logs/screenshots enter Git automatically; checkpoint commits only ever include the milestone's own allowed app/doc-decision files.

`agent/visual_qa.py` drives journeys appropriate to each milestone's `visual_key` (`engine`, `core`, `account`, `localization`, `qa`) via the Compose test tags `agent/CURRENT_TASK.md` asks each milestone to expose (`world-map`, `territory-*`, `interaction-<territory>-{1,2,…}`, `nav-*`, `design-*`, `language-*`, `engine-canvas`, `nav-account`/`auth-*`/`terms-accept`, …). It installs the local debug APK on an explicitly selected emulator only, never touches a physical device, and stops the app after the journey. It **uninstalls the app first** (not just `install -r`) so a first-run language-selection screen, where implemented, is actually reachable and exercised on every run rather than silently skipped because a previous run already configured local state — this only ever affects this one app's own data, never an emulator-wide setting.

For every milestone except `engine`, the journey runs the **full cross product** of the requested themes and languages (not each dimension independently): for each theme it explicitly taps that design option — including `system`, which used to be treated as a no-op — then for each language within it, re-enters the territories and exercises each one's required `interaction-<territory>-N` controls, not just entering and leaving. Every screenshot name is unique per combination (e.g. `territory-attention-interaction-1-bright-de`); a second capture under a name already used raises immediately rather than silently overwriting earlier evidence. The `engine` milestone's own journey requires its `engine-canvas` tag to exist — that is the entirety of its claim, so it is not optional evidence. A required tag that can't be found anywhere is a hard failure (an incomplete implementation), not skipped evidence; a genuinely optional tag (e.g. the `account` milestone's live-login state, which has no real test credentials available) is recorded as `not_verified` instead. Screenshot review is required for PASS; it does not replace the launch matrix in docs/LAUNCH_CRITERIA.md.

## Prerequisites still outstanding

- **Account milestone**: `FEELY_API_BASE` must be exported before starting, or it blocks. Even when exported, live reachability is unverified (a prior manual check returned HTTP 403 / error 1010) — the milestone's brief asks the implementing agent to build real network-error handling rather than assume success. Non-production test credentials, email-delivery/password-reset test paths, a confirmed terms-acceptance API, and Google Android client configuration remain unresolved (see docs/AUTH_INTEGRATION.md); none of these can be supplied by this automation.
- **Engine milestone**: nothing external required; it is self-contained (evaluate, then add one dependency).
- No other milestone has an external prerequisite today.

## Tests

```sh
python3 -m unittest discover -s agent/tests -v
```

These are **mocked orchestration tests**: they exercise the controller's own decision logic (milestone progression and skipping, build-repair vs. review-retry limits, scope/credential checks, checkpoint/WIP behavior, state resume, malformed-review and missing-screenshot handling) against fixtures, with `claude`/`gates`/`review` usually stubbed out. A subset runs `verify_scope()`/`checkpoint()` against a real temporary Git repository (real `git add`/`commit`/`status`, not mocked) to prove the scope-vs-checkpoint separation and extra_paths handling actually work against Git, and another subset drives `agent/visual_qa.py`'s journey logic against a scripted fake `adb` (canned uiautomator XML, no real device). None of this starts a real Claude/Codex subprocess, runs Gradle, or touches an emulator. They prove the controller's bookkeeping and the visual-QA journey logic are correct in isolation. They are **not** evidence that a real end-to-end agent cycle works — only an actual `python3 agent/loop.py --serial <emulator>` run against a live emulator, with real Claude/Codex/Gradle, demonstrates that.
