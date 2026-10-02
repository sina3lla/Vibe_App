#!/usr/bin/env python3
"""Bounded local Claude -> gates -> Codex -> Claude development cycle."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = {"type": "object", "properties": {
    "verdict": {"type": "string", "enum": ["PASS", "FIX", "BLOCKED"]},
    "summary": {"type": "string"},
    "findings": {"type": "array", "items": {"type": "string"}},
    "visual_reviewed": {"type": "boolean"}},
    "required": ["verdict", "summary", "findings", "visual_reviewed"], "additionalProperties": False}


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


def allowed_path(path):
    return path.startswith(('app/src/main/', 'app/src/test/', 'app/src/androidTest/'))


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
        self.baseline = snapshot()
        self.head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT)
        self.schema = self.run / 'review-schema.json'
        self.schema.write_text(json.dumps(SCHEMA))

    def check_stop(self):
        if (ROOT / 'agent/STOP').exists():
            raise RuntimeError('Stop file detected')
        if time.monotonic() >= self.deadline:
            raise RuntimeError('Total runtime limit reached')

    def command(self, argv, label, timeout=600, stdin=None):
        self.check_stop()
        self.log('START ' + label)
        with (self.run / (label + '.log')).open('w') as out:
            process = subprocess.Popen(argv, cwd=ROOT, env=self.env, stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,
                                       stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                if stdin:
                    process.stdin.write(stdin.encode()); process.stdin.close()
                end = time.monotonic() + timeout
                while process.poll() is None:
                    self.check_stop()
                    if time.monotonic() >= end:
                        raise RuntimeError(label + ' timed out')
                    time.sleep(1)
                if process.returncode:
                    raise RuntimeError(label + ' failed; see ' + str(self.run / (label + '.log')))
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL); process.wait()
        self.log('DONE ' + label)

    def log(self, text):
        line = time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + text
        print(line, flush=True)
        with (self.run / 'RUN_LOG.md').open('a') as out:
            out.write(line + '\n')

    def verify_scope(self):
        current = snapshot()
        changed = [p for p in set(self.baseline) | set(current) if self.baseline.get(p) != current.get(p)]
        forbidden = [p for p in changed if not allowed_path(p)]
        if forbidden:
            raise RuntimeError('Protected files changed: ' + ', '.join(forbidden))
        if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT) != self.head:
            raise RuntimeError('Git HEAD changed unexpectedly')
        if subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=ROOT).strip():
            raise RuntimeError('Unexpected index changes')

    def claude(self, prompt, label, readonly=False):
        tools = 'Read,Glob,Grep' if readonly else 'Read,Glob,Grep,Edit,Write'
        # Restricted mode confines file tools to the workspace. No shell, plugins or MCP.
        settings = {'disableAllHooks': True, 'permissions': {'deny': [
            'Read(.env*)', 'Read(local.properties)', 'Read(**/*.jks)', 'Read(**/*.keystore)',
            'Edit(agent/**)', 'Write(agent/**)', 'Edit(docs/**)', 'Write(docs/**)',
            'Edit(AGENTS.md)', 'Write(AGENTS.md)', 'Edit(CLAUDE.md)', 'Write(CLAUDE.md)',
            'Edit(**/*.gradle*)', 'Write(**/*.gradle*)', 'Edit(gradle/**)', 'Write(gradle/**)',
            'Edit(gradlew*)', 'Write(gradlew*)', 'Edit(.git/**)', 'Write(.git/**)']}}
        argv = ['claude', '-p', prompt, '--restricted', '--safe-mode', '--permission-mode', 'dontAsk',
                '--permission-prompts', 'none', '--tools', tools, '--allowedTools', tools,
                '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
                '--settings', json.dumps(settings), '--no-session-persistence', '--output-format', 'json',
                '--max-budget-usd', str(self.args.claude_budget)]
        self.command(argv, label, timeout=900)
        response = json.loads((self.run / (label + '.log')).read_text())
        if response.get('is_error') or response.get('subtype') != 'success' or response.get('permission_denials'):
            raise RuntimeError('Claude failed or encountered denied permissions: ' + label)
        if 'BLOCKED' in response.get('result', ''):
            raise RuntimeError('Claude reported BLOCKED; inspect ' + label)
        self.verify_scope()

    def gates(self, iteration):
        self.command(['git', 'diff', '--check'], f'{iteration}-diff')
        self.command(['./gradlew', '--no-daemon', 'assembleDebug', 'test', 'lintDebug', 'connectedDebugAndroidTest'], f'{iteration}-gradle', timeout=900)
        destination = self.run / f'{iteration}-visual'
        self.command([sys.executable, str(ROOT / 'agent/visual_qa.py'), '--serial', self.args.serial,
                      '--output', str(destination)], f'{iteration}-visual', timeout=300)
        return sorted(destination.glob('*.png'))

    def review(self, iteration, images):
        output = self.run / f'{iteration}-review.json'
        prompt = ('Read AGENTS.md, docs/PRODUCT_VISION.md, docs/LAUNCH_CRITERIA.md, agent/CURRENT_TASK.md. '
                  'Review the current diff and relevant source. Inspect every attached screenshot. '
                  f'This run evidence is at {self.run}. Build/test/lint and scripted visual journey succeeded. '
                  'Check evidence logs and visual manifest; do not infer untested configurations passed. '
                  'Return strict JSON for this task only. Do not execute Gradle or other agents. Do not modify files.')
        argv = ['codex', 'exec', '--ignore-user-config', '--ignore-rules', '--ephemeral',
                '--sandbox', 'read-only', '-c', 'approval_policy="never"', '--output-schema', str(self.schema),
                '--output-last-message', str(output)]
        for path in images:
            argv.extend(['--image', str(path)])
        argv.append(prompt)
        self.command(argv, f'{iteration}-codex', timeout=900)
        self.verify_scope()
        return validate_review(json.loads(output.read_text()))

    def execute(self):
        context = 'Read CLAUDE.md, docs/PRODUCT_VISION.md, docs/LAUNCH_CRITERIA.md, agent/CURRENT_TASK.md. '
        self.claude(context + 'Implement the current task. The orchestrator runs checks after you finish. Only edit app source/resources/tests. Report BLOCKED if needed.', 'implement')
        for iteration in range(1, self.args.max_reviews + 1):
            images = self.gates(iteration)
            review = self.review(iteration, images)
            self.log('REVIEW ' + review['verdict'])
            if review['verdict'] == 'BLOCKED':
                raise RuntimeError(review['summary'])
            if review['verdict'] == 'PASS':
                self.claude(context + 'Codex passed the task. Read ' + str(self.run / f'{iteration}-review.json') +
                            '. Give a concise completion handoff. Do not edit files or begin another task.', 'handoff', readonly=True)
                self.log('PASS — task complete, changes left for inspection; no commit/push/release')
                return
            if iteration == self.args.max_reviews:
                raise RuntimeError('Review retry limit reached')
            self.claude(context + 'Fix valid findings from ' + str(self.run / f'{iteration}-review.json') +
                        '. Stay within current task; explain evidence for disagreements.', f'{iteration}-fix')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True, help='Explicit emulator serial; physical devices are refused')
    parser.add_argument('--max-reviews', type=int, default=3, choices=range(1, 4))
    parser.add_argument('--minutes', type=int, default=45, choices=range(1, 121))
    parser.add_argument('--claude-budget', type=float, default=3.0, help='Per-invocation USD cap, not a combined provider cap')
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
        try:
            loop.execute()
        except (Exception, KeyboardInterrupt) as exc:
            loop.log('STOP: ' + str(exc))
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
