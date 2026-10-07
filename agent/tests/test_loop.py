"""Controller unit tests against mocked fixtures.

These test the controller's own decision logic (milestone progression, repair
limits, scope/credential checks, resume state) in isolation. They do not run
Gradle, Codex, or a real Claude subprocess, and they are not evidence that a
real end-to-end agent cycle (loop.py actually driving an emulator) works —
that can only be observed by running the loop itself against a live emulator.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch, Mock

AGENT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AGENT_DIR))

spec = importlib.util.spec_from_file_location('loop', AGENT_DIR / 'loop.py')
loop = importlib.util.module_from_spec(spec); spec.loader.exec_module(loop)
import milestones  # noqa: E402  (after sys.path setup above)

visual_qa_spec = importlib.util.spec_from_file_location('visual_qa', AGENT_DIR / 'visual_qa.py')
visual_qa = importlib.util.module_from_spec(visual_qa_spec); visual_qa_spec.loader.exec_module(visual_qa)


def fake_milestone(key='fake', controller_only=False, required_env=(), design_brief=None, extra_paths=()):
    return milestones.Milestone(
        key=key, title='Fake milestone', brief='# Current Task — fake\n\nDo the fake thing.\n',
        required_env=required_env, visual_key='core', themes=('system',), languages=('en',),
        controller_only=controller_only, design_brief=design_brief, extra_paths=extra_paths)


class ReviewValidationTests(unittest.TestCase):
    def test_missing_visual_evidence_cannot_pass(self):
        with self.assertRaises(RuntimeError):
            loop.validate_review(dict(verdict='PASS', summary='ok', findings=[], visual_reviewed=False))

    def test_unresolved_findings_cannot_pass(self):
        with self.assertRaises(RuntimeError):
            loop.validate_review(dict(verdict='PASS', summary='ok', findings=['broken'], visual_reviewed=True))

    def test_unknown_verdict_fails_closed(self):
        with self.assertRaises(RuntimeError):
            loop.validate_review(dict(verdict='APPROVED', summary='ok', findings=[], visual_reviewed=True))

    def test_malformed_missing_field_fails_closed(self):
        with self.assertRaises(RuntimeError):
            loop.validate_review(dict(verdict='PASS', summary='ok', findings=[]))

    def test_malformed_wrong_type_fails_closed(self):
        with self.assertRaises(RuntimeError):
            loop.validate_review(dict(verdict='FIX', summary='ok', findings='not-a-list', visual_reviewed=True))

    def test_fix_requires_findings(self):
        with self.assertRaises(RuntimeError):
            loop.validate_review(dict(verdict='FIX', summary='ok', findings=[], visual_reviewed=True))

    def test_blocked_does_not_require_findings_or_visual(self):
        # BLOCKED only needs to be well-formed; it is not claiming a passed check.
        result = loop.validate_review(dict(verdict='BLOCKED', summary='missing env', findings=[], visual_reviewed=False))
        self.assertEqual(result['verdict'], 'BLOCKED')


class ScopeAndCredentialTests(unittest.TestCase):
    def test_scope_rejects_build_and_control_files(self):
        for path in ['agent/loop.py', 'app/build.gradle.kts', 'gradlew', 'AGENTS.md', '.git/config']:
            self.assertFalse(loop.allowed_path(path))
        self.assertTrue(loop.allowed_path('app/src/main/example.kt'))

    def test_extra_paths_grant_exact_file_only(self):
        extra = ('app/build.gradle.kts', 'gradle/libs.versions.toml')
        self.assertTrue(loop.allowed_path('app/build.gradle.kts', extra))
        self.assertTrue(loop.allowed_path('gradle/libs.versions.toml', extra))
        self.assertFalse(loop.allowed_path('build.gradle.kts', extra))
        self.assertFalse(loop.allowed_path('gradlew', extra))
        self.assertFalse(loop.allowed_path('settings.gradle.kts', extra))

    def test_checkpoint_excludes_credentials_and_run_artifacts(self):
        self.assertFalse(loop.checkpoint_allowed('.env.local'))
        self.assertFalse(loop.checkpoint_allowed('local.properties'))
        self.assertFalse(loop.checkpoint_allowed('app/secrets/release.jks'))
        self.assertFalse(loop.checkpoint_allowed('agent/runs/20260101-000000/01-home.png'))
        self.assertTrue(loop.checkpoint_allowed('agent/CURRENT_TASK.md'))
        self.assertTrue(loop.checkpoint_allowed(loop.API_CONFIG_PATH))
        self.assertTrue(loop.checkpoint_allowed('docs/decisions/3D_ENGINE_EVALUATION.md'))
        self.assertTrue(loop.checkpoint_allowed('app/src/main/java/x.kt'))

    def test_checkpoint_extra_paths_do_not_leak_credential_exclusion(self):
        # Even an explicitly granted extra path is still refused if it matches a
        # credential suffix/prefix — belt-and-suspenders, should never occur in practice.
        self.assertFalse(loop.checkpoint_allowed('local.properties', extra=('local.properties',)))


class StopAndDeadlineTests(unittest.TestCase):
    def test_stop_file_and_deadline(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(loop, 'ROOT', Path(directory)):
            (Path(directory) / 'agent').mkdir()
            controller = object.__new__(loop.Loop)
            controller.deadline = time.monotonic() - 1
            with self.assertRaisesRegex(RuntimeError, 'runtime'):
                controller.check_stop()
            self.assertIsInstance(controller.check_stop, type(controller.check_stop))
            controller.deadline = time.monotonic() + 60
            (Path(directory) / 'agent/STOP').touch()
            with self.assertRaisesRegex(RuntimeError, 'Stop file'):
                controller.check_stop()

    def test_stop_and_deadline_raise_stop_requested_specifically(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(loop, 'ROOT', Path(directory)):
            (Path(directory) / 'agent').mkdir()
            (Path(directory) / 'agent/STOP').touch()
            controller = object.__new__(loop.Loop)
            controller.deadline = time.monotonic() + 60
            with self.assertRaises(loop.StopRequested):
                controller.check_stop()


class MissingEnvTests(unittest.TestCase):
    def test_missing_env_reports_absent_vars(self):
        milestone = fake_milestone(required_env=('TOTALLY_UNSET_VAR_FOR_TEST',))
        os.environ.pop('TOTALLY_UNSET_VAR_FOR_TEST', None)
        self.assertEqual(loop.missing_env(milestone), ['TOTALLY_UNSET_VAR_FOR_TEST'])

    def test_missing_env_empty_when_set(self):
        milestone = fake_milestone(required_env=('TOTALLY_SET_VAR_FOR_TEST',))
        os.environ['TOTALLY_SET_VAR_FOR_TEST'] = 'value'
        try:
            self.assertEqual(loop.missing_env(milestone), [])
        finally:
            del os.environ['TOTALLY_SET_VAR_FOR_TEST']

    def test_missing_env_empty_for_no_requirement(self):
        self.assertEqual(loop.missing_env(fake_milestone(required_env=())), [])


class StateResumeTests(unittest.TestCase):
    def test_load_state_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(loop, 'STATE_PATH', Path(directory) / 'nope.json'):
                self.assertEqual(loop.load_state(restart=False), {})

    def test_load_state_reads_existing_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / 'state.json'
            state_path.write_text(json.dumps({'engine': 'passed', 'core': 'in_progress'}))
            with patch.object(loop, 'STATE_PATH', state_path):
                self.assertEqual(loop.load_state(restart=False), {'engine': 'passed', 'core': 'in_progress'})

    def test_restart_flag_discards_saved_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / 'state.json'
            state_path.write_text(json.dumps({'engine': 'passed'}))
            with patch.object(loop, 'STATE_PATH', state_path):
                self.assertEqual(loop.load_state(restart=True), {})

    def test_corrupt_state_file_does_not_crash_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / 'state.json'
            state_path.write_text('{not json')
            with patch.object(loop, 'STATE_PATH', state_path):
                self.assertEqual(loop.load_state(restart=False), {})


class MilestoneRepairLimitTests(unittest.TestCase):
    """run_milestone() calls the real write_controlled(), which writes relative to the
    module-level loop.ROOT. Every test here redirects ROOT to a throwaway tempdir first,
    so nothing ever touches this repository's actual agent/CURRENT_TASK.md."""

    def setUp(self):
        self._tempdir = tempfile.TemporaryDirectory()
        self._root_patch = patch.object(loop, 'ROOT', Path(self._tempdir.name))
        self._root_patch.start()

    def tearDown(self):
        self._root_patch.stop()
        self._tempdir.cleanup()

    def _controller(self, max_build_repairs=2, max_reviews=3):
        controller = object.__new__(loop.Loop)
        controller.args = SimpleNamespace(max_build_repairs=max_build_repairs, max_reviews=max_reviews)
        controller.run = Path(self._tempdir.name) / 'evidence'
        controller.state = {}
        controller.current_milestone = None
        controller.scope_baseline = {}
        controller.checkpoint_baseline = {}
        return controller

    def test_build_repair_limit_stops_milestone_not_whole_run(self):
        controller = self._controller(max_build_repairs=2)
        milestone = fake_milestone(controller_only=True)  # skips the initial implement call
        with patch.object(controller, 'gates', side_effect=RuntimeError('gradle failed')), \
             patch.object(controller, 'claude') as claude, \
             patch.object(controller, 'log'):
            with self.assertRaisesRegex(RuntimeError, 'repair limit'):
                controller.run_milestone(milestone)
            # Exactly max_build_repairs buildfix attempts, no implement/handoff call.
            self.assertEqual(claude.call_count, 2)

    def test_review_retry_limit_stops_milestone(self):
        controller = self._controller(max_reviews=3)
        milestone = fake_milestone()
        fix_review = dict(verdict='FIX', summary='fix', findings=['bug'], visual_reviewed=True)
        with patch.object(controller, 'gates', return_value=['img.png']), \
             patch.object(controller, 'review', return_value=fix_review), \
             patch.object(controller, 'claude') as claude, \
             patch.object(controller, 'log'):
            with self.assertRaisesRegex(RuntimeError, 'retry limit'):
                controller.run_milestone(milestone)
            # 1 implement + 2 fixes (3rd FIX hits the limit before another fix call)
            self.assertEqual(claude.call_count, 3)

    def test_blocked_review_stops_immediately_without_consuming_retries(self):
        controller = self._controller(max_reviews=3)
        milestone = fake_milestone()
        blocked_review = dict(verdict='BLOCKED', summary='missing infra', findings=[], visual_reviewed=False)
        with patch.object(controller, 'gates', return_value=['img.png']), \
             patch.object(controller, 'review', return_value=blocked_review), \
             patch.object(controller, 'claude') as claude, \
             patch.object(controller, 'log'):
            with self.assertRaisesRegex(RuntimeError, 'missing infra'):
                controller.run_milestone(milestone)
            self.assertEqual(claude.call_count, 1)  # only the initial implement call

    def test_pass_checkpoints_state_and_sends_readonly_handoff(self):
        controller = self._controller()
        milestone = fake_milestone(key='core')
        pass_review = dict(verdict='PASS', summary='ok', findings=[], visual_reviewed=True)
        with patch.object(controller, 'gates', return_value=['img.png']), \
             patch.object(controller, 'review', return_value=pass_review), \
             patch.object(controller, 'claude') as claude, \
             patch.object(controller, 'checkpoint', return_value='deadbeef') as checkpoint, \
             patch.object(controller, 'save_state'), \
             patch.object(controller, 'log'):
            controller.run_milestone(milestone)
            self.assertEqual(claude.call_count, 2)  # implement + handoff
            self.assertTrue(claude.call_args.kwargs['readonly'])
            self.assertEqual(controller.state['core'], 'passed')
            checkpoint.assert_called_once()

    def test_pass_carries_milestone_extra_paths_to_review_and_handoff(self):
        # Regression for: extra_paths must reach review()'s and the readonly handoff
        # claude()'s scope check too, not just the implement/fix calls — otherwise a
        # legitimate engine-milestone Gradle change is flagged as a scope violation the
        # moment Codex reviews it or the handoff call runs.
        controller = self._controller()
        milestone = fake_milestone(key='engine', extra_paths=('app/build.gradle.kts', 'gradle/libs.versions.toml'))
        pass_review = dict(verdict='PASS', summary='ok', findings=[], visual_reviewed=True)
        with patch.object(controller, 'gates', return_value=['img.png']), \
             patch.object(controller, 'review', return_value=pass_review) as review, \
             patch.object(controller, 'claude') as claude, \
             patch.object(controller, 'checkpoint', return_value='deadbeef') as checkpoint, \
             patch.object(controller, 'save_state'), \
             patch.object(controller, 'log'):
            controller.run_milestone(milestone)
            handoff_call = claude.call_args_list[-1]
            self.assertEqual(handoff_call.kwargs.get('extra_paths'), milestone.extra_paths)
            checkpoint.assert_called_once_with('Milestone engine passed', milestone.extra_paths)
        review.assert_called_once()

    def test_milestone_not_marked_passed_when_checkpoint_raises(self):
        # Regression for: state must only say 'passed' once the checkpoint commit has
        # actually succeeded, so a failed commit doesn't leave resume believing the
        # milestone is done over an uncommitted tree.
        controller = self._controller()
        milestone = fake_milestone(key='core')
        pass_review = dict(verdict='PASS', summary='ok', findings=[], visual_reviewed=True)
        with patch.object(controller, 'gates', return_value=['img.png']), \
             patch.object(controller, 'review', return_value=pass_review), \
             patch.object(controller, 'claude'), \
             patch.object(controller, 'checkpoint', side_effect=RuntimeError('git commit failed')), \
             patch.object(controller, 'save_state') as save_state, \
             patch.object(controller, 'log'):
            with self.assertRaisesRegex(RuntimeError, 'git commit failed'):
                controller.run_milestone(milestone)
        self.assertNotIn('core', controller.state)
        save_state.assert_not_called()

    def test_scope_violation_during_implement_aborts_without_repair_loop(self):
        controller = self._controller()
        milestone = fake_milestone()
        with patch.object(controller, 'claude', side_effect=loop.ScopeViolation('bad path')), \
             patch.object(controller, 'gates') as gates, \
             patch.object(controller, 'log'):
            with self.assertRaises(loop.ScopeViolation):
                controller.run_milestone(milestone)
            gates.assert_not_called()

    def test_design_phase_writes_decision_file_before_implement(self):
        controller = self._controller()
        milestone = fake_milestone(design_brief='# design\n\nweigh the options\n')
        pass_review = dict(verdict='PASS', summary='ok', findings=[], visual_reviewed=True)
        written = {}

        def record_write(rel_path, content):
            written[rel_path] = content

        with patch.object(controller, 'write_controlled', side_effect=record_write) as write_controlled, \
             patch.object(controller, 'claude', return_value='Use SceneView/Filament 1.2.3.') as claude, \
             patch.object(controller, 'gates', return_value=['img.png']), \
             patch.object(controller, 'review', return_value=pass_review), \
             patch.object(controller, 'checkpoint', return_value=None), \
             patch.object(controller, 'save_state'), \
             patch.object(controller, 'log'):
            controller.run_milestone(milestone)
            self.assertIn('docs/decisions/3D_ENGINE_EVALUATION.md', written)
            self.assertIn('Use SceneView/Filament 1.2.3.', written['docs/decisions/3D_ENGINE_EVALUATION.md'])
            # design call must be read-only
            design_call = claude.call_args_list[0]
            self.assertTrue(design_call.kwargs.get('readonly'))


class ExecuteProgressionTests(unittest.TestCase):
    def _controller(self):
        controller = object.__new__(loop.Loop)
        controller.state = {}
        return controller

    def test_execute_skips_passed_blocks_missing_env_and_continues_independent_work(self):
        controller = self._controller()
        controller.state = {'engine': 'passed', 'core': 'passed'}
        os.environ.pop('FEELY_API_BASE', None)  # ensure the account milestone is blocked
        calls = []
        with patch.object(controller, 'run_milestone', side_effect=lambda m: calls.append(m.key)), \
             patch.object(controller, 'save_state'), \
             patch.object(controller, 'log'):
            controller.execute()
        self.assertNotIn('engine', calls)
        self.assertNotIn('core', calls)
        self.assertNotIn('account', calls)
        self.assertIn('localization', calls)
        self.assertIn('qa', calls)
        self.assertIn('release', calls)
        self.assertTrue(controller.state['account'].startswith('blocked'))

    def test_execute_runs_account_once_env_is_present(self):
        controller = self._controller()
        controller.state = {m.key: 'passed' for m in milestones.MILESTONES if m.key != 'account'}
        os.environ['FEELY_API_BASE'] = 'https://api.feel-y.com/api/v1'
        calls = []
        try:
            with patch.object(controller, 'run_milestone', side_effect=lambda m: calls.append(m.key)), \
                 patch.object(controller, 'save_state'), \
                 patch.object(controller, 'log'):
                controller.execute()
        finally:
            del os.environ['FEELY_API_BASE']
        self.assertEqual(calls, ['account'])

    def test_execute_stops_whole_run_on_genuine_milestone_failure(self):
        controller = self._controller()
        controller.state = {}
        with patch.object(controller, 'run_milestone', side_effect=RuntimeError('core: review retry limit reached')), \
             patch.object(controller, 'save_state'), \
             patch.object(controller, 'log'):
            with self.assertRaises(RuntimeError):
                controller.execute()


class GatesEvidenceTests(unittest.TestCase):
    def test_gates_rejects_empty_visual_evidence(self):
        from types import SimpleNamespace
        controller = object.__new__(loop.Loop)
        controller.run = Path(tempfile.mkdtemp())
        controller.args = SimpleNamespace(serial='emulator-5554')
        milestone = fake_milestone()
        with patch.object(controller, 'command'):  # no-op: no visual dir/pngs ever created
            with self.assertRaisesRegex(RuntimeError, 'No visual evidence'):
                controller.gates(milestone, 'fake-1')


class CheckpointWipTests(unittest.TestCase):
    def test_checkpoint_wip_marks_in_progress_and_uses_milestone_extra_paths(self):
        controller = object.__new__(loop.Loop)
        controller.current_milestone = 'engine'
        controller.state = {}
        with patch.object(controller, 'checkpoint', return_value='deadbeef') as checkpoint, \
             patch.object(controller, 'save_state'):
            result = controller.checkpoint_wip()
        self.assertEqual(result, 'deadbeef')
        self.assertEqual(controller.state['engine'], 'in_progress')
        checkpoint.assert_called_once()
        self.assertEqual(checkpoint.call_args.args[1], milestones.MILESTONES_BY_KEY['engine'].extra_paths)

    def test_checkpoint_wip_noop_without_a_current_milestone(self):
        controller = object.__new__(loop.Loop)
        controller.current_milestone = None
        self.assertIsNone(controller.checkpoint_wip())


class ApiConfigGenerationTests(unittest.TestCase):
    def test_api_config_kt_escapes_and_embeds_url(self):
        content = loop.api_config_kt('https://api.feel-y.com/api/v1')
        self.assertIn('object ApiConfig', content)
        self.assertIn('https://api.feel-y.com/api/v1', content)
        self.assertIn('package com.example.eso1.data.auth', content)


class RealGitCheckpointTests(unittest.TestCase):
    """Regression coverage for separating scope tracking from checkpoint tracking,
    against a real temporary Git repository — not a mock — so `git add`/`git commit`/
    `git status` actually run. This still does not exercise a real Claude/Codex/Gradle
    cycle; see the module docstring."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        self._git('init', '-q')
        self._git('config', 'user.email', 'test@example.com')
        self._git('config', 'user.name', 'Test')
        (self.repo / 'app/src/main').mkdir(parents=True)
        (self.repo / 'agent').mkdir()
        (self.repo / 'app/src/main/Placeholder.kt').write_text('// placeholder\n')
        # Mirror the real repo's .gitignore so agent/runs/ (where evidence/logs live) is
        # invisible to snapshot()/verify_scope(), exactly as in production.
        (self.repo / '.gitignore').write_text('/agent/runs/\n')
        self._git('add', '.')
        self._git('commit', '-q', '-m', 'initial')
        self._root_patch = patch.object(loop, 'ROOT', self.repo)
        self._root_patch.start()

    def tearDown(self):
        self._root_patch.stop()
        self.tempdir.cleanup()

    def _git(self, *args):
        subprocess.run(['git', *args], cwd=self.repo, check=True, capture_output=True)

    def _git_status(self):
        return subprocess.check_output(['git', 'status', '--porcelain'], cwd=self.repo).decode()

    def _controller(self):
        controller = object.__new__(loop.Loop)
        controller.run = self.repo / 'agent/runs/testrun'
        controller.run.mkdir(parents=True)
        controller.schema = controller.run / 'review-schema.json'
        initial = loop.snapshot()
        controller.scope_baseline = initial
        controller.checkpoint_baseline = initial
        controller.head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.repo)
        return controller

    def test_controller_owned_file_is_actually_checkpointed(self):
        # The bug: write_controlled() used to fold its own write into the same baseline
        # checkpoint() diffs against, making the file look unchanged and never staged.
        controller = self._controller()
        controller.write_controlled('agent/CURRENT_TASK.md', '# task\n')
        commit = controller.checkpoint('test checkpoint', extra_paths=())
        self.assertIsNotNone(commit)
        committed = subprocess.check_output(
            ['git', 'show', '--stat', '--name-only', 'HEAD'], cwd=self.repo).decode()
        self.assertIn('agent/CURRENT_TASK.md', committed)

    def test_resume_tree_is_clean_after_checkpoint(self):
        controller = self._controller()
        controller.write_controlled('agent/CURRENT_TASK.md', '# task\n')
        (self.repo / 'app/src/main/New.kt').write_text('// new\n')
        controller.checkpoint('milestone passed', extra_paths=())
        self.assertEqual(self._git_status(), '')

    def test_scope_verification_ignores_controller_owned_file(self):
        controller = self._controller()
        controller.write_controlled('agent/CURRENT_TASK.md', '# task\n')
        # Must not raise: agent/CURRENT_TASK.md is not in allowed_path/extra_paths, but it
        # is controller-owned — the Claude subprocess never touched it.
        controller.verify_scope(extra_paths=())

    def test_engine_extra_path_change_does_not_trigger_scope_violation(self):
        controller = self._controller()
        (self.repo / 'app/build.gradle.kts').write_text('// dependency added\n')
        controller.verify_scope(extra_paths=('app/build.gradle.kts',))

    def test_extra_path_change_without_the_grant_is_still_a_violation(self):
        controller = self._controller()
        (self.repo / 'app/build.gradle.kts').write_text('// unauthorized\n')
        with self.assertRaises(loop.ScopeViolation):
            controller.verify_scope(extra_paths=())

    def test_unrelated_forbidden_file_is_a_violation_even_with_an_extra_path_granted(self):
        controller = self._controller()
        (self.repo / 'settings.gradle.kts').write_text('// not allowed\n')
        with self.assertRaises(loop.ScopeViolation):
            controller.verify_scope(extra_paths=('app/build.gradle.kts',))

    def test_checkpoint_stages_the_granted_extra_path_file(self):
        controller = self._controller()
        (self.repo / 'app/build.gradle.kts').write_text('// dependency added\n')
        commit = controller.checkpoint('engine passed', extra_paths=('app/build.gradle.kts',))
        self.assertIsNotNone(commit)
        committed = subprocess.check_output(
            ['git', 'show', '--stat', '--name-only', 'HEAD'], cwd=self.repo).decode()
        self.assertIn('app/build.gradle.kts', committed)

    def test_review_does_not_flag_milestones_own_extra_path_change(self):
        controller = self._controller()
        (self.repo / 'app/build.gradle.kts').write_text('// dependency added\n')
        milestone = fake_milestone(key='engine', extra_paths=('app/build.gradle.kts',))
        output_path = controller.run / 'engine-1-review.json'
        output_path.write_text(json.dumps(dict(verdict='PASS', summary='ok', findings=[], visual_reviewed=True)))
        with patch.object(controller, 'command'):
            result = controller.review(milestone, 'engine-1', ['fake.png'])
        self.assertEqual(result['verdict'], 'PASS')

    def test_handoff_claude_call_does_not_flag_milestones_own_extra_path_change(self):
        controller = self._controller()
        controller.args = SimpleNamespace(claude_budget=3.0)
        (self.repo / 'app/build.gradle.kts').write_text('// dependency added\n')
        response = {'subtype': 'success', 'is_error': False, 'permission_denials': [], 'result': 'done'}
        (controller.run / 'handoff.log').write_text(json.dumps(response))
        with patch.object(controller, 'command'):
            controller.claude('prompt', 'handoff', readonly=True, extra_paths=('app/build.gradle.kts',))


class VisualQAJourneyTests(unittest.TestCase):
    """Exercises agent/visual_qa.py's Journey/run() logic against a scripted fake adb
    (no real emulator), proving the strengthened journey behavior directly."""

    def setUp(self):
        # Journey.tap()/capture() sleep briefly to let a real device settle; the full
        # theme x language x interaction matrix would make this suite minutes slow
        # otherwise, so time itself is sped up, not the behavior under test.
        self._sleep_patch = patch('time.sleep')
        self._sleep_patch.start()

    def tearDown(self):
        self._sleep_patch.stop()

    def _journey(self, tags_present):
        out = Path(tempfile.mkdtemp())
        xml = ('<hierarchy>' + ''.join(
            f'<node resource-id="{t}" text="" content-desc="" bounds="[0,0][100,50]" enabled="true"/>'
            for t in tags_present) + '</hierarchy>').encode()
        journey = visual_qa.Journey(Path('/fake/adb'), 'emulator-5554', out)

        def fake_command(*parts):
            if parts[:2] == ('shell', 'cat'):
                return xml
            if parts[:2] == ('exec-out', 'screencap'):
                return b'FAKE-PNG'
            return b''

        journey.command = Mock(side_effect=fake_command)
        return journey

    def test_engine_journey_requires_the_canvas_tag(self):
        journey = self._journey(tags_present=['back'])  # no engine-canvas
        with self.assertRaisesRegex(RuntimeError, 'engine-canvas'):
            visual_qa.run(journey, 'engine', ['system'], ['en'])

    def test_engine_journey_captures_the_canvas_when_present(self):
        journey = self._journey(tags_present=['engine-canvas'])
        visual_qa.run(journey, 'engine', ['system'], ['en'])
        self.assertIn('engine-canvas', journey.captured)

    def test_apply_theme_explicitly_taps_system_mode(self):
        # Regression: the old code treated 'system' as a no-op (no tap, no capture).
        journey = self._journey(tags_present=['nav-settings', 'design-system', 'back'])
        journey.apply_theme('system', '-system')
        self.assertIn('settings-theme-system', journey.captured)

    def test_duplicate_screenshot_name_is_rejected(self):
        journey = self._journey(tags_present=[])
        journey.capture('world-map-system-en')
        with self.assertRaisesRegex(RuntimeError, 'Duplicate screenshot'):
            journey.capture('world-map-system-en')

    def test_handle_first_run_taps_language_when_present(self):
        journey = self._journey(tags_present=['language-en'])
        journey.handle_first_run('en')
        self.assertIn('00-first-run-language-en', journey.captured)

    def test_handle_first_run_is_a_noop_when_already_configured(self):
        journey = self._journey(tags_present=[])  # no first-run picker reachable
        journey.handle_first_run('en')
        self.assertEqual(journey.captured, [])

    def test_territory_interaction_tags_are_required(self):
        # territory-attention and its first interaction exist, but not the second —
        # this must fail, not silently skip the missing evidence.
        journey = self._journey(tags_present=['territory-attention', 'interaction-attention-1', 'back'])
        with self.assertRaisesRegex(RuntimeError, 'interaction-attention-2'):
            journey.territories('-x')

    def test_core_journey_covers_full_theme_language_cross_product_with_unique_names(self):
        tags = ['nav-settings', 'back', 'nav-discoveries',
                'design-system', 'design-bright', 'language-en', 'language-de']
        for name in visual_qa.TERRITORIES:
            tags.append('territory-' + name)
            for i in range(1, visual_qa.INTERACTIONS_PER_TERRITORY + 1):
                tags.append(f'interaction-{name}-{i}')
        journey = self._journey(tags_present=tags)
        visual_qa.run(journey, 'core', ['system', 'bright'], ['en', 'de'])
        # 2 themes x 2 languages must each leave their own distinctly-named evidence.
        self.assertIn('territory-attention-interaction-1-bright-de', journey.captured)
        self.assertIn('territory-attention-interaction-1-system-en', journey.captured)
        self.assertEqual(len(journey.captured), len(set(journey.captured)))


if __name__ == '__main__':
    unittest.main()
