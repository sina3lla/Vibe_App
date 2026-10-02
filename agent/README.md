# Autonomous development loop

Run from the clean `agent/autonomous-dev` branch:

```sh
python3 agent/loop.py --serial emulator-5554
```

Claude implements CURRENT_TASK; the controller builds/tests/lints, runs connected Android tests and captures an emulator journey; Codex reviews the diff and screenshots; Claude fixes findings or provides a read-only completion handoff. Fixes repeat verification. PASS stops the task. It does not automatically invent another task, commit, push, or release.

Defaults: three reviews maximum, 45 minutes overall, 15 minutes per agent/build invocation, and $3 per Claude invocation. The Claude cap is per invocation; Codex uses the authenticated account and has no monetary cap here. At most four Claude and three Codex calls per run. Existing CLI account/model defaults are used (Codex ignores personal configuration for isolation). Runtime limits are not precise spend limits.

Requires Python 3, Git, current Claude with `--restricted`/`--safe-mode`, Codex with `--ignore-user-config`, Android SDK/adb, Java, and a running emulator. The local default SDK and Android Studio Java paths support this Mac. Override JAVA_HOME or ANDROID_HOME when necessary. Authenticate both CLIs interactively before running. Never put credentials in this repo.

Claude receives only Read/Glob/Grep/Edit/Write, restricted to its workspace, with hooks/customizations and MCP disabled. It cannot invoke a shell. Codex runs read-only with approvals disabled. The controller rejects changes outside app source/tests before executing Gradle. This is a local development boundary, not a hostile-code container: Gradle and instrumentation execute app code on your machine/emulator. Use a disposable environment before applying this to untrusted projects. The controller never changes permissions to get around failure.

Stop with Ctrl-C or create `agent/STOP`; the controller checks it every second during child processes and terminates their process group. Remove STOP deliberately before restarting. A lock prevents simultaneous runs. Any failed command, malformed result, missing required evidence, denied permission, protected-file change, human blocker, timeout, or exhausted reviews stops with nonzero exit status. Failed build/QA stops for diagnosis rather than being mistaken for review PASS. Work is preserved; no automatic reset or stash.

Logs, reviews, screenshots, UI trees and manifests live under ignored `agent/runs/<timestamp>/`. See each run's RUN_LOG.md. `agent/REVIEW.md` is historical context only; current reviews are uniquely named within the run. Start only from a clean commit; review and commit the resulting diff before a subsequent task. No logs/screenshots enter Git automatically.

Visual QA only installs the local debug APK on an explicitly selected emulator. It does not clear app data, modify global display settings, or touch a physical device. Use a test emulator whose camera permission for this app is not granted. It checks Home, Vibrant start/stop, Mannequin entry, Ascension simulated completion/restart and Back, capturing eight states. It stops the app after the journey. See the manifest for limitations. Screenshot review is required for PASS; it does not replace the launch matrix in docs/LAUNCH_CRITERIA.md.

Verification of the controller's failure handling:

```sh
python3 -m unittest discover -s agent/tests -v
```
