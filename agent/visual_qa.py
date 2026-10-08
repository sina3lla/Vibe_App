#!/usr/bin/env python3
"""Emulator-only interaction journeys; screenshots and UI trees are review evidence.

Replaces the old journey hard-coded to the Vibrant/Mannequin/Ascension ritual
screens. Journeys are now selected per milestone (--milestone) and repeated
for every requested theme x language combination (--themes, --languages) —
not each dimension in isolation — so "both themes" and "both languages"
evidence (docs/LAUNCH_CRITERIA.md H and F) genuinely covers the matrix for
the milestones that change those surfaces, instead of two independent passes
that never actually combine.

Navigation is driven by the stable Compose test tags agent/CURRENT_TASK.md
(generated from agent/milestones.py) asks each milestone to expose via
semantics { testTagsAsResourceId = true }: world-map, territory-*,
interaction-<territory>-{1,2,...}, nav-*, language-*, design-*, quiet-toggle,
back, engine-canvas, and the account-milestone tags nav-account/auth-*/
terms-accept. A tag required by the milestone's journey that cannot be found
is a real failure, not skipped evidence — "missing screenshots" must never
read as a pass (see agent/README.md and agent/tests/test_loop.py).

The app is uninstalled before each run (not just `install -r`) so a first-run
language-selection screen, if implemented, is actually reachable and
exercised instead of silently skipped because a prior run already configured
the app's local state. This does not touch emulator-wide display settings.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'com.example.eso1'
TERRITORIES = ['attention', 'needs', 'boundaries', 'perspective', 'rest']
INTERACTIONS_PER_TERRITORY = 2


class Journey:
    def __init__(self, adb, serial, out):
        self.adb = adb
        self.serial = serial
        self.out = out
        self.captured = []
        self.not_verified = []

    def command(self, *parts):
        return subprocess.check_output([str(self.adb), '-s', self.serial, *parts], timeout=45)

    def tree(self):
        self.command('shell', 'uiautomator', 'dump', '/sdcard/feelanything-qa.xml')
        return self.command('shell', 'cat', '/sdcard/feelanything-qa.xml')

    def capture(self, name):
        if name in self.captured:
            raise RuntimeError('Duplicate screenshot name (would silently overwrite evidence): ' + name)
        time.sleep(0.8)
        (self.out / (name + '.png')).write_bytes(self.command('exec-out', 'screencap', '-p'))
        data = self.tree()
        (self.out / (name + '.xml')).write_bytes(data)
        self.captured.append(name)
        return data

    def find(self, tag, data=None):
        data = data if data is not None else self.tree()
        for node in ET.fromstring(data).iter('node'):
            rid = node.get('resource-id', '').rsplit('/', 1)[-1]
            if rid == tag or node.get('text') == tag or node.get('content-desc') == tag:
                if node.get('enabled') == 'true':
                    bounds = list(map(int, re.findall(r'\d+', node.get('bounds', ''))))
                    if len(bounds) == 4:
                        return bounds
        return None

    def read_status(self, tag, data=None):
        """Find a node BY resource-id == tag and return ITS OWN text/content-desc value
        (unlike find(), which matches the tag against a node's identity to locate a
        control to tap). Used for a node that reports a status value through its own
        text, e.g. engine-render-status reporting the literal string 'native' or
        'fallback' — a mechanical, independently-checkable claim rather than something
        left to a screenshot's visual similarity or the implementing agent's own report."""
        data = data if data is not None else self.tree()
        for node in ET.fromstring(data).iter('node'):
            rid = node.get('resource-id', '').rsplit('/', 1)[-1]
            if rid == tag:
                return node.get('text') or node.get('content-desc') or ''
        return None

    def tap(self, tag, required=True, data=None):
        bounds = self.find(tag, data)
        if bounds is None:
            if required:
                raise RuntimeError('Expected control missing: ' + tag)
            self.not_verified.append(tag + ' (not reachable)')
            return False
        x1, y1, x2, y2 = bounds
        self.command('shell', 'input', 'tap', str((x1 + x2) // 2), str((y1 + y2) // 2))
        time.sleep(0.7)
        return True

    def handle_first_run(self, language):
        # Best-effort: only the 'core' milestone onward actually implements this screen,
        # and only a freshly uninstalled app will show it. Absence here is not itself a
        # failure — it just means there was nothing to dismiss before continuing.
        if self.find('language-' + language) is not None:
            self.tap('language-' + language, required=False)
            self.capture('00-first-run-language-' + language)

    def go_settings(self):
        self.tap('nav-settings')

    def apply_theme(self, theme, suffix):
        # Always an explicit tap, including 'system' — the setting must be genuinely
        # selected and captured, not assumed from whatever the emulator defaulted to.
        self.go_settings()
        self.tap('design-' + theme)
        self.capture('settings-theme' + suffix)
        self.tap('back')

    def apply_language(self, lang, suffix):
        self.go_settings()
        self.tap('language-' + lang)
        self.capture('settings-language' + suffix)
        self.tap('back')

    def territories(self, suffix):
        for name in TERRITORIES:
            self.tap('territory-' + name)
            self.capture('territory-' + name + suffix)
            for index in range(1, INTERACTIONS_PER_TERRITORY + 1):
                self.tap(f'interaction-{name}-{index}')
                self.capture(f'territory-{name}-interaction-{index}{suffix}')
            self.tap('back')

    def core_pass(self, suffix):
        self.capture('world-map' + suffix)
        self.territories(suffix)
        self.tap('nav-discoveries')
        self.capture('discoveries' + suffix)
        self.tap('back')

    def account_pass(self, required, suffix):
        if not self.tap('nav-account', required=required):
            return
        self.capture('account-entry' + suffix)
        if self.tap('terms-accept', required=False):
            self.capture('account-terms' + suffix)
        self.tap('auth-submit', required=False)
        self.capture('account-validation' + suffix)
        self.not_verified += [
            'live login with real credentials' + suffix,
            'email verification delivery' + suffix,
            'password reset delivery' + suffix,
            'google login' + suffix,
        ]
        self.tap('back', required=False)


def run(journey, milestone, themes, languages):
    journey.handle_first_run(languages[0] if languages else 'en')
    journey.capture('01-home')
    if milestone == 'engine':
        # The engine milestone only proves a dependency + minimal harness; the five
        # territories, nav-*, and settings tags do not exist yet at this point in the
        # sequence. The harness itself is this milestone's entire claim, so its tag is
        # required evidence, not best-effort.
        journey.tap('engine-canvas')
        data = journey.capture('engine-canvas')
        # Mechanical acceptance check: a Compose-drawn fallback (or a missing status
        # node) must not pass just because something visible was captured. See
        # docs/reference/FILAMAT_ANDROID.md and agent/runs/20261008-232956/
        # engine-1-review.json, which Codex BLOCKED for exactly this gap.
        status = journey.read_status('engine-render-status', data)
        if status != 'native':
            raise RuntimeError(
                "engine-render-status reports {!r}, not 'native' — a Compose fallback "
                "or missing status node does not satisfy native-rendering acceptance "
                "for this milestone".format(status))
        return
    if milestone not in ('core', 'account', 'localization', 'qa'):
        raise RuntimeError('Unknown milestone journey: ' + milestone)
    for theme in themes:
        theme_suffix = f'-{theme}'
        journey.apply_theme(theme, theme_suffix)
        for lang in languages:
            suffix = f'-{theme}-{lang}'
            journey.apply_language(lang, suffix)
            if milestone in ('core', 'localization', 'qa'):
                journey.core_pass(suffix)
            if milestone == 'account':
                journey.account_pass(required=True, suffix=suffix)
            if milestone == 'qa':
                # Best-effort: account may not have passed yet, or may be blocked on
                # FEELY_API_BASE — qa validates whatever already exists, not what should.
                journey.account_pass(required=False, suffix=suffix + '-qa')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--serial', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--milestone', required=True, choices=['engine', 'core', 'account', 'localization', 'qa'])
    p.add_argument('--themes', default='system')
    p.add_argument('--languages', default='en')
    args = p.parse_args()
    if not re.fullmatch(r'emulator-\d+', args.serial):
        p.error('Only an explicitly selected emulator is allowed')
    themes = [t for t in args.themes.split(',') if t]
    languages = [l for l in args.languages.split(',') if l]
    adb = Path(os.environ.get('ANDROID_HOME', str(Path.home() / 'Library/Android/sdk'))) / 'platform-tools/adb'
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)

    def command(*parts):
        return subprocess.check_output([str(adb), '-s', args.serial, *parts], timeout=45)

    if command('shell', 'getprop', 'ro.kernel.qemu').strip() != b'1':
        raise RuntimeError('Target did not identify as emulator')
    # Uninstall first (best-effort; the app may not be present yet) so this app's own
    # local state — including any first-run language choice — starts fresh every time.
    # This never touches emulator-wide display/density/font settings.
    subprocess.run([str(adb), '-s', args.serial, 'uninstall', PACKAGE],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=45)
    command('install', str(ROOT / 'app/build/outputs/apk/debug/app-debug.apk'))
    command('shell', 'am', 'force-stop', PACKAGE)
    command('shell', 'am', 'start', '-W', '-n', PACKAGE + '/.MainActivity')

    journey = Journey(adb, args.serial, out)
    try:
        run(journey, args.milestone, themes, languages)
        if not journey.captured:
            raise RuntimeError('No screenshots captured; refusing to report evidence')
        manifest = {
            'serial': args.serial,
            'package': PACKAGE,
            'milestone': args.milestone,
            'themes': themes,
            'languages': languages,
            'result': 'PASS',
            'coverage': journey.captured,
            'not_verified': journey.not_verified + ['TalkBack', 'font/size/orientation matrix', 'process recreation'],
            'display': command('shell', 'wm', 'size').decode(),
            'density': command('shell', 'wm', 'density').decode(),
            'font_scale': command('shell', 'settings', 'get', 'system', 'font_scale').decode(),
        }
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    finally:
        command('shell', 'am', 'force-stop', PACKAGE)
        command('shell', 'rm', '-f', '/sdcard/feelanything-qa.xml')


if __name__ == '__main__':
    main()
