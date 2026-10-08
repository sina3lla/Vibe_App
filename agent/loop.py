#!/usr/bin/env python3
"""Bounded, resumable local Claude -> gates -> Codex -> Claude milestone sequence.

Drives the milestones in agent/milestones.py in order. Each milestone is its
own bounded implement/gate/review/fix cycle; a PASS checkpoints (local commit
only, never pushed) and the controller continues automatically to the next
milestone. A milestone whose required_env is missing is marked blocked and
skipped so independent milestones can still proceed; an exhausted repair/
review budget or the stop file/timeout stops the whole run for diagnosis.
Progress is recorded in agent/runs/milestones-state.json so a later
invocation resumes instead of restarting.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

import milestones

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / 'agent/runs/milestones-state.json'
API_CONFIG_PATH = 'app/src/main/java/com/example/eso1/data/auth/ApiConfig.kt'
CREDENTIAL_PREFIXES = ('.env', 'local.properties')
CREDENTIAL_SUFFIXES = ('.jks', '.keystore')

SCHEMA = {"type": "object", "properties": {
    "verdict": {"type": "string", "enum": ["PASS", "FIX", "BLOCKED"]},
    "summary": {"type": "string"},
    "findings": {"type": "array", "items": {"type": "string"}},
    "visual_reviewed": {"type": "boolean"}},
    "required": ["verdict", "summary", "findings", "visual_reviewed"], "additionalProperties": False}


class StopRequested(RuntimeError):
    """Stop file or overall runtime deadline; never silently swallowed or retried."""


class ScopeViolation(RuntimeError):
    """Claude touched a forbidden path or git state changed unexpectedly; left uncommitted for inspection."""


class StatusContractError(RuntimeError):
    """A Claude response's STATUS: line was missing, duplicated, or BLOCKED without a
    REASON: — a malformed contract, never silently treated as OK or as BLOCKED."""


def validate_review(value):
    if set(value) != set(SCHEMA['required']):
        raise RuntimeError('Malformed review fields')
    if value['verdict'] not in ('PASS', 'FIX', 'BLOCKED') or type(value['visual_reviewed']) is not bool:
        raise RuntimeError('Malformed review verdict')
    if not isinstance(value['summary'], str) or not isinstance(value['findings'], list) or not all(isinstance(x, str) for x in value['findings']):
        raise RuntimeError('Malformed review content')
    if value['verdict'] == 'PASS' and (value['findings'] or not value['visual_reviewed']):
        raise RuntimeError('PASS requires visual inspection and no unresolved findings')
    if value['verdict'] == 'FIX' and not value['findings']:
        raise RuntimeError('FIX requires actionable findings')
    return value


def allowed_path(path, extra=()):
    if path in extra:
        return True
    return path.startswith(('app/src/main/', 'app/src/test/', 'app/src/androidTest/'))


CONTROLLER_OWNED_PATHS = ('agent/CURRENT_TASK.md', API_CONFIG_PATH, 'docs/decisions/3D_ENGINE_EVALUATION.md')

# Named gradle/build files a milestone may be granted explicit, individual write access
# to via Milestone.extra_paths. Globs (wrapper binary/scripts) are never lifted, even then.
GRADLE_NAMED_FILES = (
    'build.gradle.kts', 'app/build.gradle.kts', 'settings.gradle.kts', 'gradle.properties',
    'gradle/libs.versions.toml', 'gradle/gradle-daemon-jvm.properties',
)
GRADLE_ALWAYS_PROTECTED_GLOBS = ('gradlew*', 'gradle/wrapper/**')

# Bare, root-level filenames also handed to the Claude subprocess's permission deny list.
BARE_ROOT_FILES = ('AGENTS.md', 'CLAUDE.md')


def anchored(pattern):
    """Root-anchor a bare filename/glob for the Claude subprocess's permission deny list.

    This is the actual root cause of the 2026-10-08 engine-milestone failure: a deny
    pattern with no '/' in it (e.g. 'build.gradle.kts', meant to protect only the ROOT
    build file) is matched gitignore-style — at ANY directory depth — by Claude Code's
    settings.json permission engine, so it also denied edits to app/build.gradle.kts
    even though that exact path was explicitly granted via Milestone.extra_paths. A
    pattern already containing a non-trailing '/' (e.g. 'app/build.gradle.kts',
    'gradle/wrapper/**') is already root-relative under that same matching convention
    and is returned unchanged. See agent/tests/test_loop.py's PermissionDenyListTests."""
    return pattern if '/' in pattern else '/' + pattern


def checkpoint_allowed(path, extra=()):
    if path.startswith(CREDENTIAL_PREFIXES) or path.endswith(CREDENTIAL_SUFFIXES):
        return False
    return allowed_path(path, extra) or path in CONTROLLER_OWNED_PATHS


def snapshot():
    paths = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).decode().split('\0')
    result = {}
    for name in paths:
        if name:
            p = ROOT / name
            if p.is_symlink():
                raise RuntimeError('Symlink in project: ' + name)
            result[name] = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
    return result


def load_state(restart):
    if restart or not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def missing_env(milestone):
    return [v for v in milestone.required_env if not os.environ.get(v)]


def build_deny_list(extra_paths=()):
    """The Claude subprocess's permission deny list for one milestone. A standalone,
    directly testable function — see claude(), which just passes this to --settings."""
    deny = [
        'Read(.env*)', 'Read(local.properties)', 'Read(**/*.jks)', 'Read(**/*.keystore)',
        'Edit(agent/**)', 'Write(agent/**)', 'Edit(docs/**)', 'Write(docs/**)',
        'Edit(.git/**)', 'Write(.git/**)']
    for name in BARE_ROOT_FILES:
        deny += [f'Edit({anchored(name)})', f'Write({anchored(name)})']
    # Gradle/build files stay denied by name; a milestone's extra_paths can lift the deny
    # for the exact named files it was explicitly scoped to touch (never a glob, and never
    # the wrapper itself) — verify_scope() still rejects anything else.
    for pattern in GRADLE_NAMED_FILES:
        if pattern not in extra_paths:
            deny += [f'Edit({anchored(pattern)})', f'Write({anchored(pattern)})']
    for pattern in GRADLE_ALWAYS_PROTECTED_GLOBS:
        deny += [f'Edit({anchored(pattern)})', f'Write({anchored(pattern)})']
    return deny


# Known agent/loop.py command labels, by suffix, mapped to a human-readable (actor, action)
# pair for live progress output and STATUS.md — see describe_label().
LABEL_ACTORS = {
    'design': ('Claude', 'producing a read-only design recommendation'),
    'implement': ('Claude', 'implementing the milestone'),
    'buildfix': ('Claude', 'repairing a build/test/lint/visual-QA failure'),
    'fix': ('Claude', 'addressing Codex review findings'),
    'handoff': ('Claude', 'writing a read-only completion handoff'),
    'diff': ('automated checks', 'running git diff --check'),
    'gradle': ('automated checks', 'running Gradle assemble/test/lint/connected tests'),
    'visual': ('automated checks', 'running the emulator screenshot journey'),
    'codex': ('Codex', 'independently reviewing the diff and screenshots'),
}


def describe_label(label):
    """('engine', 'Claude', 'implementing the milestone') from a command label like
    'engine-implement' or 'engine-2-buildfix'. Falls back to a plain description for an
    unrecognized label rather than guessing."""
    milestone_key = label.split('-', 1)[0]
    for suffix, (actor, action) in LABEL_ACTORS.items():
        if label.endswith('-' + suffix):
            return milestone_key, actor, action
    return milestone_key, 'controller', label


SECRET_PATTERNS = [
    re.compile(r'(?i)\b(?:api[_-]?key|token|secret|password)\b\s*[:=]\s*\S+'),
    re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b'),
    re.compile(r'\bghp_[A-Za-z0-9]{30,}\b'),
    re.compile(r'\bxox[baprs]-[A-Za-z0-9-]+\b'),
    re.compile(r'\bBearer\s+[A-Za-z0-9._-]{10,}\b'),
    re.compile(r'[A-Za-z0-9+/]{60,}={0,2}'),  # a long base64-looking blob
]


def redact(text):
    """Best-effort scrub of secret-shaped substrings before any subprocess output is
    printed to the terminal or written into RUN_LOG.md/STATUS.md. Not a guarantee — real
    secrets should never be in this project's build output in the first place — but this
    is the one place raw stdout/stderr is surfaced outside the per-step log file, so it
    errs toward redacting too much rather than too little."""
    for pattern in SECRET_PATTERNS:
        text = pattern.sub('[redacted]', text)
    return text


def tail_summary(path, max_chars=400):
    """A short, redacted summary of a log file's tail, or '' if it can't be read. Used
    both for live heartbeats ('here is new output since the last update') and for
    specific failure reasons, instead of a bare 'see the log' pointer."""
    try:
        text = path.read_text(errors='replace')
    except OSError:
        return ''
    text = redact(text)
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return ''
    hints = [line for line in lines if re.search(r'FAILED|error:|Exception|Error:|denied', line, re.I)]
    chosen = hints[-3:] if hints else lines[-3:]
    summary = ' | '.join(chosen)
    return summary[:max_chars]


def describe_denial(denial):
    """A readable '<Tool>(<target>)' for one permission_denials entry. Different tools
    put their target under different keys (Edit/Write use file_path; Glob/Grep use
    pattern/path) — a naive `.get('file_path', '?')` renders a Glob denial as the
    useless 'Glob(?)', as seen in agent/runs/20261008-223002/engine-1-buildfix.log."""
    tool_name = denial.get('tool_name', '?')
    tool_input = denial.get('tool_input') or {}
    if 'file_path' in tool_input:
        target = tool_input['file_path']
    else:
        parts = [f'{k}={v}' for k, v in tool_input.items() if k in ('pattern', 'path')]
        target = ', '.join(parts) if parts else '?'
    return f'{tool_name}({target})'


def claude_failure_reason(response, label):
    """A specific reason a claude() call didn't succeed at the infrastructure level
    (permission denial, non-success subtype) — instead of the previous combined generic
    'Claude failed or encountered denied permissions: <label>' message that gave no hint
    which permission or which path was actually denied.

    This deliberately does NOT look for the word BLOCKED anywhere in the response text.
    That used to be a substring search over the whole narrative, which false-positived
    on a historical/narrative mention — see agent/runs/20261008-235732/engine-design.log,
    where Claude completed successfully and said so, but mentioned in passing that a
    *past Codex review* had BLOCKED. Whether Claude itself is currently blocked is
    decided separately, from an explicit STATUS: contract — see parse_claude_status()."""
    denials = response.get('permission_denials') or []
    if denials:
        described = sorted({describe_denial(d) for d in denials})
        return f"Claude ({label}) was denied permission to: {', '.join(described)}"
    if response.get('is_error') or response.get('subtype') != 'success':
        return f"Claude ({label}) did not complete successfully (subtype={response.get('subtype')!r})"
    return None


# Appended to every prompt sent to the Claude subprocess (see claude()) so every phase —
# design, implement, buildfix, fix, handoff — is asked for the same machine-parsed
# completion contract, instead of the controller guessing a genuine blocker from
# free-form narrative. Markdown emphasis (*, _, `) around the label/value is tolerated;
# the line's actual format is specified explicitly so a compliant response is simple.
STATUS_CONTRACT_INSTRUCTION = (
    "\n\nEnd your reply with exactly one status line, after a blank line, in this exact "
    "format and nothing else on that line: `STATUS: OK` if nothing currently blocks this "
    "phase, or `STATUS: BLOCKED` followed on the next line by `REASON: <one-sentence "
    "reason>` if something outside your available tools/scope currently prevents "
    "completing this phase. STATUS reports only your own present ability to finish this "
    "phase right now — never a past review's verdict, a historical event, another "
    "agent's status, or something you merely discuss in passing. Mentioning the word "
    "\"blocked\" anywhere else in your narrative does not set this status; only the "
    "STATUS: line itself does."
)

_STATUS_LINE = re.compile(r'(?im)^[\s*_`]*STATUS[\s*_`]*:[\s*_`]*(OK|BLOCKED)[\s*_`]*$')
_REASON_LINE = re.compile(r'(?im)^[\s*_`]*REASON[\s*_`]*:[\s*_`]*(.+?)[\s*_`]*$')


def parse_claude_status(text, label):
    """Parse the STATUS:/REASON: completion contract out of a Claude response's result
    text. Returns (status, reason, narrative) where status is 'OK' or 'BLOCKED', reason
    is None for OK or the one-sentence reason for BLOCKED, and narrative is the response
    text with the contract line(s) removed (so callers that store/display the response —
    e.g. the engine-design capture into docs/decisions/3D_ENGINE_EVALUATION.md, or
    log_handoff_entry's implementation-claim excerpt — don't carry the raw contract
    markup). Raises StatusContractError if the contract is missing, duplicated, or
    BLOCKED without a reason — those are surfaced as their own distinct failure, never
    silently treated as OK or as a genuine blocker."""
    matches = list(_STATUS_LINE.finditer(text))
    if not matches:
        raise StatusContractError(f'Claude ({label}) response did not include a STATUS: line')
    if len(matches) > 1:
        raise StatusContractError(f'Claude ({label}) response included more than one STATUS: line')
    status = matches[0].group(1).upper()
    narrative = (text[:matches[0].start()] + text[matches[0].end():]).strip()
    if status == 'OK':
        return 'OK', None, narrative
    reasons = _REASON_LINE.findall(text)
    if not reasons or not reasons[-1].strip():
        raise StatusContractError(f'Claude ({label}) reported STATUS: BLOCKED without a REASON: line')
    reason = reasons[-1].strip()
    narrative = _REASON_LINE.sub('', narrative).strip()
    return 'BLOCKED', reason, narrative


DYNAMIC_VERSION_PATTERN = re.compile(r'["\']([^"\']*\+[^"\']*|latest\.release|latest\.integration)["\']')


def find_dynamic_versions(extra_paths):
    """Scan a milestone's own granted files (never anything outside them) for a
    dynamic/wildcard dependency version ('1.+', 'latest.release', 'latest.integration').
    Returns a list of 'path:line: content' strings, empty if none found. This is a
    mechanical, fail-fast guard — not just brief wording — for exactly the mistake in
    agent/runs/20261008-223002/engine-1-buildfix.log (an unresolved pin was patched to
    a dynamic range instead of being verified)."""
    problems = []
    for rel_path in extra_paths:
        path = ROOT / rel_path
        if not path.is_file():
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if DYNAMIC_VERSION_PATTERN.search(line):
                problems.append(f'{rel_path}:{lineno}: {stripped}')
    return problems


def api_config_kt(base_url):
    escaped = base_url.replace('\\', '\\\\').replace('"', '\\"')
    return (
        '// Generated by agent/loop.py from the FEELY_API_BASE environment value.\n'
        '// Do not hand-edit; rerunning the controller overwrites this file.\n'
        'package com.example.eso1.data.auth\n\n'
        'object ApiConfig {\n'
        f'    const val BASE_URL: String = "{escaped}"\n'
        '}\n'
    )


class Loop:
    def __init__(self, args):
        self.args = args
        self.deadline = time.monotonic() + args.minutes * 60
        self.run = ROOT / 'agent/runs' / time.strftime('%Y%m%d-%H%M%S')
        self.run.mkdir(parents=True, exist_ok=False)
        self.env = os.environ.copy()
        self.env.setdefault('JAVA_HOME', '/Applications/Android Studio.app/Contents/jbr/Contents/Home')
        self.env['ANDROID_SERIAL'] = args.serial
        self.env['PATH'] = str(Path.home() / '.local/bin') + ':' + self.env['PATH']
        # Two separately-named trackers over the same kind of snapshot, intentionally not
        # shared: scope_baseline is what verify_scope() diffs against to catch the Claude
        # subprocess touching a forbidden path; checkpoint_baseline is what checkpoint()
        # diffs against to decide what to `git add`. write_controlled() must not update
        # either — a controller-written file (CURRENT_TASK.md, the engine decision doc,
        # ApiConfig.kt) needs to show up as "changed" to checkpoint() so it actually gets
        # committed, while verify_scope() ignores those specific paths outright (see
        # CONTROLLER_OWNED_PATHS) rather than by making them look unchanged.
        initial = snapshot()
        self.scope_baseline = initial
        self.checkpoint_baseline = initial
        self.head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT)
        self.schema = self.run / 'review-schema.json'
        self.schema.write_text(json.dumps(SCHEMA))
        self.state = load_state(args.restart)
        self.current_milestone = None
        self.current_actor = None
        self.current_action = None
        self.last_implementation_claim = ''
        self.last_review = None

    def save_state(self):
        STATE_PATH.write_text(json.dumps(self.state, indent=2))

    def check_stop(self):
        if (ROOT / 'agent/STOP').exists():
            raise StopRequested('Stop file detected')
        if time.monotonic() >= self.deadline:
            raise StopRequested('Total runtime limit reached')

    HEARTBEAT_SECONDS = 30

    def command(self, argv, label, timeout=600, stdin=None):
        self.check_stop()
        milestone_key, actor, action = describe_label(label)
        self.current_actor, self.current_action = actor, action
        log_path = self.run / (label + '.log')
        self.log(f'START {label} — {milestone_key} · {actor} · {action} (timeout {timeout}s)')
        start = time.monotonic()
        last_heartbeat = start
        with log_path.open('w') as out:
            process = subprocess.Popen(argv, cwd=ROOT, env=self.env, stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,
                                       stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                if stdin:
                    process.stdin.write(stdin.encode()); process.stdin.close()
                end = start + timeout
                while process.poll() is None:
                    self.check_stop()
                    now = time.monotonic()
                    if now - last_heartbeat >= self.HEARTBEAT_SECONDS:
                        self.heartbeat(milestone_key, actor, action, label, start, end, now)
                        last_heartbeat = now
                    if now >= end:
                        raise RuntimeError(f'{label} timed out after {timeout}s running {action}')
                    time.sleep(1)
                if process.returncode:
                    summary = tail_summary(log_path)
                    detail = f': {summary}' if summary else ''
                    raise RuntimeError(f'{label} failed (exit {process.returncode}, {action}){detail} — see {log_path}')
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL); process.wait()
        self.log(f'DONE {label} ({int(time.monotonic() - start)}s)')

    def heartbeat(self, milestone_key, actor, action, label, start, end, now):
        """A live 'still here' terminal line during a long step — never a fabricated
        percentage or a claim of progress the controller hasn't actually observed."""
        elapsed = int(now - start)
        remaining = max(0, int(end - now))
        new_output = tail_summary(self.run / (label + '.log'))
        status = f'last output: {new_output}' if new_output else 'process still running; no new output to show yet'
        print(f'[{time.strftime("%H:%M:%S")}] {milestone_key} · {actor} · {action} · '
              f'{elapsed}s elapsed, {remaining}s until step timeout · {status}', flush=True)
        self.write_status('running')

    def log(self, text):
        line = time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + text
        print(line, flush=True)
        with (self.run / 'RUN_LOG.md').open('a') as out:
            out.write(line + '\n')

    def log_handoff_entry(self, milestone, label, review):
        """A concise, structured RUN_LOG.md entry at each Claude -> checks -> Codex ->
        Claude handoff: what Claude claimed, what was actually (independently) checked,
        the review verdict, and what happens next. The raw per-step logs and the Codex
        review JSON are preserved untouched alongside this summary, not replaced by it."""
        claim = self.last_implementation_claim.strip().replace('\n', ' ')
        if len(claim) > 300:
            claim = claim[:300] + '…'
        manifest_path = self.run / f'{label}-visual' / 'manifest.json'
        lines = [
            '',
            f'### {milestone.key} / {label} — {time.strftime("%Y-%m-%d %H:%M:%S")}',
            f'- **Claude\'s implementation claim (not independently verified by itself):** {claim or "(no implement/fix call this round — controller-only step)"}',
            f'- **Independently checked:** build/test/lint/connected Android tests, and the emulator screenshot journey — see `{self.run / (label + "-gradle.log")}` and `{manifest_path}`.',
            f'- **Codex review verdict:** {review["verdict"]} — {review["summary"]}',
        ]
        if review['findings']:
            lines.append('- **Findings:**')
            lines += [f'  - {f}' for f in review['findings']]
        next_step = {
            'PASS': 'milestone recorded passed once its checkpoint commit succeeds; controller advances to the next milestone.',
            'FIX': 'Claude attempts a fix for the findings above; checks and review repeat.',
            'BLOCKED': 'run stops for diagnosis — see "Current blocker" in agent/runs/STATUS.md.',
        }[review['verdict']]
        lines.append(f'- **Next:** {next_step}')
        lines.append(f'- Raw Codex review: `{self.run / (label + "-review.json")}`')
        with (self.run / 'RUN_LOG.md').open('a') as out:
            out.write('\n'.join(lines) + '\n')

    def _is_pushed(self, commit):
        if not commit:
            return 'n/a (no checkpoint yet)'
        try:
            upstream = subprocess.check_output(
                ['git', 'rev-parse', '@{u}'], cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
        except subprocess.CalledProcessError:
            return 'unknown (no upstream tracking branch configured)'
        return 'yes' if upstream == commit else 'no (local only — the controller never pushes automatically)'

    def write_status(self, state_label, blocker=None, needs_user_action=False, next_step=None):
        """Rewrites agent/runs/STATUS.md (controller-owned, gitignored) so the current
        state of a run is understandable without reading source or logs. Called on
        start, on every heartbeat, after every review, and on exit."""
        commit = self.head.decode().strip() if isinstance(self.head, bytes) else str(self.head)
        completed = [k for k in milestones.MILESTONE_ORDER if self.state.get(k) == 'passed']
        remaining = [k for k in milestones.MILESTONE_ORDER if self.state.get(k) != 'passed']
        lines = [
            '# Autonomous loop status', '',
            '_Controller-generated; overwritten throughout the run. A stale timestamp below'
            ' does not by itself prove a process is still running — check that a'
            ' `python3 agent/loop.py` process actually exists (e.g. `pgrep -fl agent/loop.py`)'
            ' before assuming so._', '',
            f'- Run ID: `{self.run.name}`',
            f'- Last updated: {time.strftime("%Y-%m-%d %H:%M:%S")}',
            f'- State: **{state_label}**',
        ]
        if self.current_milestone:
            lines += [
                f'- Current milestone: `{self.current_milestone}`',
                f'- Current actor: {self.current_actor or "—"}',
                f'- Current action: {self.current_action or "—"}',
            ]
        else:
            lines.append('- Current milestone: none (between milestones, or not yet started)')
        lines += [
            '', '## Milestones',
            '- Completed: ' + (', '.join(completed) if completed else 'none yet'),
            '- Remaining: ' + (', '.join(remaining) if remaining else 'none — all passed'),
        ]
        for key in milestones.MILESTONE_ORDER:
            lines.append(f'  - `{key}`: {self.state.get(key, "not started")}')
        lines += ['', '## Latest verified result']
        if self.last_review:
            lines.append(
                f'- `{self.last_review["milestone"]}` / `{self.last_review["label"]}` — '
                f'verdict **{self.last_review["verdict"]}**: {self.last_review["summary"]}')
            lines.append(f'  - Evidence: `{self.last_review["log"]}`, `{self.last_review["manifest"]}`')
        else:
            lines.append('- No milestone has completed a review yet in this run.')
        lines += ['', '## Current blocker', f'- {blocker}' if blocker else '- None.']
        lines += ['', '## Is user action needed?']
        lines.append(f'- **Yes** — {next_step}' if needs_user_action else '- No — the controller is proceeding on its own.')
        lines += [
            '', '## Checkpoint',
            f'- Latest commit: `{commit[:12]}`',
            f'- Pushed to remote: {self._is_pushed(commit)}',
        ]
        status_path = ROOT / 'agent/runs/STATUS.md'
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text('\n'.join(lines) + '\n')

    def write_controlled(self, rel_path, content):
        """Write a controller-owned file (acceptance criteria, generated config, the
        engine decision doc). Deliberately does not touch scope_baseline or
        checkpoint_baseline — see the comment in __init__ for why."""
        path = ROOT / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def verify_scope(self, extra_paths=()):
        current = snapshot()
        changed = [p for p in set(self.scope_baseline) | set(current) if self.scope_baseline.get(p) != current.get(p)]
        changed = [p for p in changed if p not in CONTROLLER_OWNED_PATHS]
        forbidden = [p for p in changed if not allowed_path(p, extra_paths)]
        if forbidden:
            raise ScopeViolation('Protected files changed: ' + ', '.join(forbidden))
        if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT) != self.head:
            raise ScopeViolation('Git HEAD changed unexpectedly')
        if subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=ROOT).strip():
            raise ScopeViolation('Unexpected index changes')

    def checkpoint(self, message, extra_paths=()):
        """Local-only commit of the current controller-owned + allowed app changes.
        Never pushes. Returns the new commit hash, or None if nothing changed."""
        current = snapshot()
        changed = sorted(p for p in set(current) | set(self.checkpoint_baseline) if self.checkpoint_baseline.get(p) != current.get(p))
        stage = [p for p in changed if checkpoint_allowed(p, extra_paths)]
        if not stage:
            return None
        subprocess.check_output(['git', 'add', '--'] + stage, cwd=ROOT)
        subprocess.check_output(['git', 'commit', '-m', message], cwd=ROOT)
        fresh = snapshot()
        self.scope_baseline = fresh
        self.checkpoint_baseline = fresh
        self.head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT)
        return self.head.decode().strip()

    def checkpoint_wip(self):
        if not self.current_milestone:
            return None
        extra = milestones.MILESTONES_BY_KEY[self.current_milestone].extra_paths
        self.state[self.current_milestone] = 'in_progress'
        self.save_state()
        return self.checkpoint(f'WIP checkpoint: {self.current_milestone} interrupted (not reviewed/passed)', extra)

    def claude(self, prompt, label, readonly=False, extra_paths=()):
        tools = 'Read,Glob,Grep' if readonly else 'Read,Glob,Grep,Edit,Write'
        # Restricted mode confines file tools to the workspace. No shell, plugins or MCP.
        settings = {'disableAllHooks': True, 'permissions': {'deny': build_deny_list(extra_paths)}}
        argv = ['claude', '-p', prompt + STATUS_CONTRACT_INSTRUCTION, '--restricted', '--safe-mode',
                '--permission-mode', 'dontAsk', '--permission-prompts', 'none', '--tools', tools,
                '--allowedTools', tools, '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
                '--settings', json.dumps(settings), '--no-session-persistence', '--output-format', 'json',
                '--max-budget-usd', str(self.args.claude_budget)]
        self.command(argv, label, timeout=900)
        response = json.loads((self.run / (label + '.log')).read_text())
        reason = claude_failure_reason(response, label)
        if reason:
            raise RuntimeError(f'{reason} — see {self.run / (label + ".log")}')
        log_path = self.run / (label + '.log')
        try:
            status, blocked_reason, narrative = parse_claude_status(response.get('result', ''), label)
        except StatusContractError as exc:
            raise RuntimeError(f'{exc} — see {log_path}') from exc
        if status == 'BLOCKED':
            raise RuntimeError(f'Claude ({label}) reported a current blocker: {blocked_reason} — see {log_path}')
        self.verify_scope(extra_paths)
        self.last_implementation_claim = narrative
        return self.last_implementation_claim

    def gates(self, milestone, label):
        self.command(['git', 'diff', '--check'], f'{label}-diff')
        if milestone.extra_paths:
            dynamic = find_dynamic_versions(milestone.extra_paths)
            if dynamic:
                # Fail fast, before spending a Gradle run, on exactly the mistake in
                # agent/runs/20261008-223002: a dynamic/wildcard version instead of a
                # verified exact pin.
                raise RuntimeError('Dynamic/unpinned dependency version(s) are not allowed: ' + '; '.join(dynamic))
        self.command(['./gradlew', '--no-daemon', 'assembleDebug', 'test', 'lintDebug', 'connectedDebugAndroidTest'], f'{label}-gradle', timeout=900)
        destination = self.run / f'{label}-visual'
        self.command([sys.executable, str(ROOT / 'agent/visual_qa.py'), '--serial', self.args.serial,
                      '--output', str(destination), '--milestone', milestone.visual_key,
                      '--themes', ','.join(milestone.themes), '--languages', ','.join(milestone.languages)],
                     f'{label}-visual', timeout=900)  # theme x language x territory-interaction matrix is large
        images = sorted(destination.glob('*.png'))
        if not images:
            raise RuntimeError('No visual evidence produced for ' + label)
        return images

    def review(self, milestone, label, images):
        output = self.run / f'{label}-review.json'
        prompt = ('Read AGENTS.md, docs/PRODUCT_VISION.md, docs/LAUNCH_CRITERIA.md, agent/CURRENT_TASK.md. '
                  f'This is milestone "{milestone.key}" ({milestone.title}) of a multi-milestone build; '
                  'review only this milestone\'s bounded scope, not the full release. '
                  'Review the current diff and relevant source. Inspect every attached screenshot. '
                  f'This run evidence is at {self.run}. Build/test/lint and the scripted interaction journey succeeded. '
                  f'Read {destination_manifest(self.run, label)} for themes/languages covered and its not_verified list. '
                  'Check evidence logs and the visual manifest; do not infer untested configurations passed. '
                  'Return strict JSON for this milestone only. Do not execute Gradle or other agents. Do not modify files.'
                  + (f' {milestone.review_focus}' if milestone.review_focus else ''))
        argv = ['codex', 'exec', '--ignore-user-config', '--ignore-rules', '--ephemeral',
                '--sandbox', 'read-only', '-c', 'approval_policy="never"', '--output-schema', str(self.schema),
                '--output-last-message', str(output)]
        for path in images:
            argv.extend(['--image', str(path)])
        # `--image <FILE>...` is variadic, so a trailing positional PROMPT argument with
        # no leading '-' is ambiguous — codex's clap parser swallows it into the image
        # list instead of treating it as PROMPT, then falls back to (empty) stdin and
        # fails with "No prompt provided via stdin." `--` ends option/variadic parsing
        # unambiguously; the lone `-` after it is the documented way to tell codex to
        # read PROMPT from stdin, which command() supplies via stdin=prompt below.
        argv += ['--', '-']
        self.command(argv, f'{label}-codex', timeout=900, stdin=prompt)
        # Codex is read-only and writes nothing, but a prior Claude call in this same
        # milestone may legitimately have touched milestone.extra_paths (e.g. engine's
        # one Gradle dependency) — that diff is still outstanding until checkpoint(),
        # so verify_scope must be told about it here too or it misreads it as a violation.
        self.verify_scope(milestone.extra_paths)
        review = validate_review(json.loads(output.read_text()))
        self.last_review = {
            'milestone': milestone.key, 'label': label, 'verdict': review['verdict'],
            'summary': review['summary'], 'log': str(self.run / f'{label}-codex.log'),
            'manifest': destination_manifest(self.run, label),
        }
        self.log_handoff_entry(milestone, label, review)
        self.write_status('running')
        return review

    def write_launch_checklist(self):
        lines = [
            '# Launch status snapshot — controller-generated, not a release decision', '',
            "Generated by agent/loop.py from this run's recorded milestone outcomes. "
            'Missing evidence is reported as NOT VERIFIED, never as a pass. This file states gate '
            'status only; it does not claim owner endorsement, clinical effectiveness, or launch '
            'readiness (see docs/LAUNCH_CRITERIA.md).', '',
        ]
        for m in milestones.MILESTONES:
            status = self.state.get(m.key, 'not started')
            lines.append(f'- **{m.title}** (`{m.key}`): {status}')
        lines += [
            '',
            '## Known gaps carried from docs/AUTH_INTEGRATION.md and docs/LAUNCH_CRITERIA.md', '',
            '- Live reachability of the FeelY API base was not independently verified in automation '
            '(a prior manual check returned HTTP 403 / error 1010).',
            '- Backend-side AGB access enforcement and recording of the presented language are '
            'owner-reported, not independently confirmed in this preparation cycle.',
            '- Email delivery, password-reset delivery, and Google Android client configuration '
            'remain unverified.',
            '- Content-sourcing review for factual explanatory copy is tracked in each milestone\'s '
            'implement/fix logs under this run directory, not merged into docs/ automatically.',
            '- No public release, store listing, signing, or payment flow is in scope here.', '',
        ]
        (self.run / 'LAUNCH_CHECKLIST.md').write_text('\n'.join(lines))

    def run_milestone(self, milestone):
        self.current_milestone = milestone.key
        extra = milestone.extra_paths
        self.log('MILESTONE START ' + milestone.key)
        self.write_status('running')
        context = 'Read CLAUDE.md, docs/PRODUCT_VISION.md, docs/LAUNCH_CRITERIA.md, agent/CURRENT_TASK.md. '
        if milestone.design_brief:
            self.write_controlled('agent/CURRENT_TASK.md', milestone.design_brief.rstrip() + '\n')
            recommendation = self.claude(
                context + 'Produce your recommendation as this response\'s final text; you cannot write files '
                'in this read-only phase.', milestone.key + '-design', readonly=True)
            self.write_controlled(
                'docs/decisions/3D_ENGINE_EVALUATION.md',
                '# 3D engine evaluation — ' + time.strftime('%Y-%m-%d') + '\n\n'
                'Captured verbatim from the design-phase agent response below. This is a working '
                'recommendation for the controller to act on next, not an owner-approved architecture '
                'decision or a claim that the chosen approach has been benchmarked on real hardware.\n\n'
                '---\n\n' + recommendation.strip() + '\n')
        self.write_controlled('agent/CURRENT_TASK.md', milestone.full_brief())
        if milestone.key == 'account':
            self.write_controlled(API_CONFIG_PATH, api_config_kt(os.environ['FEELY_API_BASE']))
        if not milestone.controller_only:
            self.claude(context + 'Implement the current task. The orchestrator runs checks after you finish. '
                        'Only edit app source/resources/tests' + (' plus the exact extra files named in your '
                        'task brief' if extra else '') + '. Use your STATUS: contract to report a genuine '
                        'current blocker if one exists.',
                        milestone.key + '-implement', extra_paths=extra)
        build_attempts = 0
        review_round = 0
        attempt = 0
        while True:
            attempt += 1
            label = f'{milestone.key}-{attempt}'
            try:
                images = self.gates(milestone, label)
            except StopRequested:
                raise
            except ScopeViolation:
                raise
            except Exception as exc:
                build_attempts += 1
                if build_attempts > self.args.max_build_repairs:
                    raise RuntimeError(f'{milestone.key}: build/test/lint/visual repair limit reached: {exc}')
                self.log(f'GATE FAILURE {milestone.key}: {exc}')
                self.claude(context + f'Build, test, lint, or the scripted interaction journey failed: {exc}. '
                            'Fix the underlying problem; stay within the current task. Your tools are already '
                            'confined to this repository — do not attempt to search, read, or guess at anything '
                            'outside it (e.g. the home directory) to work around a failure; that will be denied '
                            'and wastes the attempt. Never resolve an unresolved/unverified dependency version by '
                            'switching to a dynamic or wildcard constraint (e.g. "1.+", "latest.release") — if you '
                            'cannot verify an exact version from inside the repository, state precisely what '
                            'needs external verification in your completion report instead.', f'{label}-buildfix',
                            extra_paths=extra)
                continue
            if milestone.key == 'release':
                self.write_launch_checklist()
            review_round += 1
            review = self.review(milestone, label, images)
            self.log('REVIEW ' + review['verdict'] + ' (' + milestone.key + ')')
            if review['verdict'] == 'BLOCKED':
                raise RuntimeError(milestone.key + ': ' + review['summary'])
            if review['verdict'] == 'PASS':
                self.claude(context + 'Codex passed this milestone. Read ' + str(self.run / f'{label}-review.json') +
                            '. Give a concise completion handoff. Do not edit files or begin another milestone.',
                            f'{milestone.key}-handoff', readonly=True, extra_paths=extra)
                # Checkpoint before recording 'passed': if the commit fails for any reason,
                # the milestone must not be marked done over an uncommitted tree — the next
                # resume should retry it, not skip it.
                commit = self.checkpoint(f'Milestone {milestone.key} passed', extra)
                self.state[milestone.key] = 'passed'
                self.save_state()
                self.log('MILESTONE PASS ' + milestone.key + (' commit ' + commit if commit else ' (nothing to commit)'))
                self.current_milestone = None
                self.write_status('running')
                return
            if review_round >= self.args.max_reviews:
                raise RuntimeError(milestone.key + ': review retry limit reached')
            self.claude(context + 'Fix valid findings from ' + str(self.run / f'{label}-review.json') +
                        '. Stay within current task; explain evidence for disagreements.', f'{label}-fix',
                        extra_paths=extra)

    def execute(self):
        blocked = {}
        for milestone in milestones.MILESTONES:
            if self.state.get(milestone.key) == 'passed':
                continue
            missing = missing_env(milestone)
            if missing:
                reason = 'missing env: ' + ','.join(missing)
                self.state[milestone.key] = 'blocked: ' + reason
                self.save_state()
                self.log('MILESTONE BLOCKED ' + milestone.key + ' (' + reason + ')')
                blocked[milestone.key] = reason
                continue
            self.run_milestone(milestone)
        if blocked:
            self.log('RUN COMPLETE WITH BLOCKED MILESTONES: ' + ', '.join(f'{k} ({v})' for k, v in blocked.items()))
        else:
            self.log('RUN COMPLETE — ALL MILESTONES PASSED')


def destination_manifest(run, label):
    return str(run / f'{label}-visual' / 'manifest.json')


def print_exit_summary(state_label, reason, commit, checkpoint_note, serial):
    """The plain-language explanation printed on exit: why it stopped, what was saved,
    what remains unverified, and how to resume. Separate from the terminal RUN_LOG.md
    trail so it reads as a summary even if the scrollback above has been lost."""
    print()
    print('=' * 70)
    if state_label == 'complete':
        print('Run complete.')
        print('See agent/runs/STATUS.md for the final milestone-by-milestone outcome,')
        print('and this run\'s RUN_LOG.md for the detailed handoff trail.')
        print('Nothing was pushed automatically — review the checkpoint commits yourself before pushing.')
    else:
        verb = {'stopped': 'Stopped', 'failed': 'Failed'}[state_label]
        print(f'{verb}: {reason}')
        if checkpoint_note == 'saved':
            print(f'Work up to this point was saved in a local, unpushed WIP checkpoint commit ({commit[:12]}).')
        elif checkpoint_note == 'nothing_to_save':
            print('No new WIP checkpoint was needed — nothing uncommitted needed saving.')
        elif checkpoint_note == 'failed':
            print('A WIP checkpoint could not be made — see RUN_LOG.md for why; nothing was discarded, but it is not yet committed.')
        elif checkpoint_note == 'left_uncommitted':
            print('Left uncommitted on purpose — a scope violation is not auto-committed; a human should')
            print('inspect the unexpected change before anything is folded into Git history.')
        print('Nothing beyond the last checkpoint has been independently verified by Codex.')
        print(f'To resume: remove agent/STOP if present, then rerun: python3 agent/loop.py --serial {serial}')
    print('A timestamp in agent/runs/STATUS.md does not by itself prove a process is still')
    print('alive — check that a `python3 agent/loop.py` process actually exists')
    print('(e.g. `pgrep -fl agent/loop.py`) before assuming the run is still going.')
    print('=' * 70)


def abort(loop_obj, args, state_label, reason, make_checkpoint, next_step):
    """Shared exit path for every non-success stop (scope violation, STOP file/timeout,
    Ctrl+C, or a genuine error): logs it, optionally WIP-checkpoints, updates
    STATUS.md, and prints the plain-language summary. Returns the process exit code."""
    loop_obj.log(f'STOP ({state_label}): {reason}')
    commit = None
    if make_checkpoint:
        try:
            commit = loop_obj.checkpoint_wip()
            if commit:
                loop_obj.log('WIP checkpoint committed: ' + commit)
                checkpoint_note = 'saved'
            else:
                checkpoint_note = 'nothing_to_save'
        except Exception as checkpoint_exc:
            loop_obj.log('WIP checkpoint failed: ' + str(checkpoint_exc))
            checkpoint_note = 'failed'
    else:
        loop_obj.log('Left uncommitted for inspection (scope violation) — nothing staged or committed.')
        checkpoint_note = 'left_uncommitted'
    try:
        loop_obj.write_status(state_label, blocker=reason, needs_user_action=True, next_step=next_step)
    except Exception as status_exc:
        loop_obj.log('STATUS.md update failed: ' + str(status_exc))
    print_exit_summary(state_label, reason, commit, checkpoint_note, args.serial)
    return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True, help='Explicit emulator serial; physical devices are refused')
    parser.add_argument('--max-reviews', type=int, default=3, choices=range(1, 4), help='Codex review rounds per milestone')
    parser.add_argument('--max-build-repairs', type=int, default=2, choices=range(1, 4), help='Build/test/lint/visual repair attempts per milestone')
    parser.add_argument('--minutes', type=int, default=180, choices=range(1, 481), help='Overall runtime limit for this invocation; hitting it stops cleanly and resumes next run')
    parser.add_argument('--claude-budget', type=float, default=3.0, help='Per-invocation USD cap, not a combined provider cap')
    parser.add_argument('--restart', action='store_true', help='Discard saved milestone progress and start the sequence over (does not discard committed app code)')
    args = parser.parse_args()
    if not args.serial.startswith('emulator-') or not 0 < args.claude_budget <= 10:
        parser.error('Use an emulator serial and Claude budget between 0 and 10')
    if subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT).decode().strip() != 'agent/autonomous-dev':
        parser.error('Expected agent/autonomous-dev branch')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
        parser.error('Start from a clean committed working tree')
    (ROOT / 'agent/runs').mkdir(exist_ok=True)
    with (ROOT / 'agent/runs/loop.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error('Another loop is running')
        loop = Loop(args)
        loop.write_status('running')
        try:
            loop.execute()
        except ScopeViolation as exc:
            return abort(loop, args, 'failed', str(exc), make_checkpoint=False,
                         next_step='Inspect the forbidden-path change by hand (see RUN_LOG.md and the '
                                   'step log named in the error above). Nothing was committed. Resolve '
                                   'it — or revert the unexpected change — then rerun.')
        except StopRequested as exc:
            return abort(loop, args, 'stopped', str(exc), make_checkpoint=True,
                         next_step=f'Remove agent/STOP if present, then rerun: python3 agent/loop.py --serial {args.serial}')
        except KeyboardInterrupt:
            return abort(loop, args, 'stopped', 'Interrupted by Ctrl+C', make_checkpoint=True,
                         next_step=f'Rerun when ready: python3 agent/loop.py --serial {args.serial}')
        except Exception as exc:
            return abort(loop, args, 'failed', str(exc), make_checkpoint=True,
                         next_step='Read the specific failure reason above (and its referenced log), fix '
                                    f'the underlying cause, then rerun: python3 agent/loop.py --serial {args.serial}')
        loop.write_status('complete')
        print_exit_summary('complete', None, None, None, args.serial)
    return 0


if __name__ == '__main__':
    sys.exit(main())
