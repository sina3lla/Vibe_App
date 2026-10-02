#!/usr/bin/env python3
"""Emulator-only smoke journey; screenshots and UI trees are review evidence."""
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


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--serial', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if not re.fullmatch(r'emulator-\d+', args.serial):
        p.error('Only an explicitly selected emulator is allowed')
    adb = Path(os.environ.get('ANDROID_HOME', str(Path.home() / 'Library/Android/sdk'))) / 'platform-tools/adb'
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)

    def command(*parts):
        return subprocess.check_output([str(adb), '-s', args.serial, *parts], timeout=45)

    def tree():
        command('shell', 'uiautomator', 'dump', '/sdcard/feelanything-qa.xml')
        return command('shell', 'cat', '/sdcard/feelanything-qa.xml')

    def capture(name):
        time.sleep(0.8)
        (out / (name + '.png')).write_bytes(command('exec-out', 'screencap', '-p'))
        data = tree(); (out / (name + '.xml')).write_bytes(data)
        return data

    def tap(label):
        data = tree()
        for node in ET.fromstring(data).iter('node'):
            if node.get('text') == label or node.get('content-desc') == label:
                bounds = list(map(int, re.findall(r'\d+', node.get('bounds', ''))))
                if len(bounds) == 4 and node.get('enabled') == 'true':
                    x1, y1, x2, y2 = bounds
                    command('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))
                    time.sleep(0.7); return
        raise RuntimeError('Expected accessible control missing: ' + label)

    if command('shell', 'getprop', 'ro.kernel.qemu').strip() != b'1':
        raise RuntimeError('Target did not identify as emulator')
    command('install', '-r', str(ROOT / 'app/build/outputs/apk/debug/app-debug.apk'))
    command('shell', 'am', 'force-stop', PACKAGE)
    # Do not clear user data or alter emulator display settings.
    command('shell', 'am', 'start', '-W', '-n', PACKAGE + '/.MainActivity')
    try:
        capture('01-home')
        tap('Vibrant'); capture('02-vibrant')
        tap('BEGIN'); capture('03-vibrant-active'); tap('SEAL'); tap('Back')
        tap('Mannequin'); capture('04-mannequin'); tap('Back')
        tap('Ascension'); data = capture('05-ascension-entry')
        if b'Use simulated view' in data:
            tap('Use simulated view')
        elif b'Camera on' in data:
            raise RuntimeError('Use an emulator with camera permission not granted for the simulated-path QA')
        capture('06-ascension-simulated')
        for label in ['Lock signal', 'Begin rite', 'Mark seal', 'Mark seal', 'Mark seal', 'Send to light']:
            tap(label)
        data = capture('07-ascension-complete')
        if b'Restart' not in data:
            raise RuntimeError('Completion was not reached')
        tap('Restart'); tap('Back'); capture('08-home-return')
        manifest = {'serial': args.serial, 'package': PACKAGE, 'result': 'PASS',
                    'coverage': ['home', 'vibrant start/stop', 'mannequin entry', 'ascension simulated complete/restart', 'back'],
                    'not_verified': ['real camera', 'TalkBack', 'font/size/orientation matrix', 'audio quality', 'process recreation'],
                    'display': command('shell', 'wm', 'size').decode(),
                    'density': command('shell', 'wm', 'density').decode(),
                    'font_scale': command('shell', 'settings', 'get', 'system', 'font_scale').decode()}
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    finally:
        command('shell', 'am', 'force-stop', PACKAGE)
        command('shell', 'rm', '-f', '/sdcard/feelanything-qa.xml')


if __name__ == '__main__':
    main()
