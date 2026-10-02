import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('loop', Path(__file__).resolve().parents[1] / 'loop.py')
loop = importlib.util.module_from_spec(spec); spec.loader.exec_module(loop)

class ControllerTests(unittest.TestCase):
    def test_missing_visual_evidence_cannot_pass(self):
        with self.assertRaises(RuntimeError):
            loop.validate_review(dict(verdict='PASS', summary='ok', findings=[], visual_reviewed=False))

    def test_unresolved_findings_cannot_pass(self):
        with self.assertRaises(RuntimeError):
            loop.validate_review(dict(verdict='PASS', summary='ok', findings=['broken'], visual_reviewed=True))

    def test_unknown_verdict_fails_closed(self):
        with self.assertRaises(RuntimeError):
            loop.validate_review(dict(verdict='APPROVED', summary='ok', findings=[], visual_reviewed=True))

    def test_scope_rejects_build_and_control_files(self):
        for path in ['agent/loop.py', 'app/build.gradle.kts', 'gradlew', 'AGENTS.md', '.git/config']:
            self.assertFalse(loop.allowed_path(path))
        self.assertTrue(loop.allowed_path('app/src/main/example.kt'))

    def test_stop_file_and_deadline(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(loop, 'ROOT', Path(directory)):
            (Path(directory) / 'agent').mkdir()
            controller = object.__new__(loop.Loop)
            controller.deadline = time.monotonic() - 1
            with self.assertRaisesRegex(RuntimeError, 'runtime'):
                controller.check_stop()
            controller.deadline = time.monotonic() + 60
            (Path(directory) / 'agent/STOP').touch()
            with self.assertRaisesRegex(RuntimeError, 'Stop file'):
                controller.check_stop()

    def test_review_limit_does_not_call_extra_fixer(self):
        from types import SimpleNamespace
        controller = object.__new__(loop.Loop)
        controller.args = SimpleNamespace(max_reviews=3)
        controller.run = Path('/tmp/test-evidence')
        review = dict(verdict='FIX', summary='fix', findings=['bug'], visual_reviewed=True)
        with patch.object(controller, 'claude') as claude, patch.object(controller, 'gates', return_value=[]), patch.object(controller, 'review', return_value=review), patch.object(controller, 'log'):
            with self.assertRaisesRegex(RuntimeError, 'retry limit'):
                controller.execute()
            self.assertEqual(claude.call_count, 3)

    def test_pass_requires_claude_readonly_handoff(self):
        from types import SimpleNamespace
        controller = object.__new__(loop.Loop)
        controller.args = SimpleNamespace(max_reviews=3)
        controller.run = Path('/tmp/test-evidence')
        review = dict(verdict='PASS', summary='ok', findings=[], visual_reviewed=True)
        with patch.object(controller, 'claude') as claude, patch.object(controller, 'gates', return_value=[]), patch.object(controller, 'review', return_value=review), patch.object(controller, 'log'):
            controller.execute()
            self.assertEqual(claude.call_count, 2)
            self.assertTrue(claude.call_args.kwargs['readonly'])

if __name__ == '__main__':
    unittest.main()
