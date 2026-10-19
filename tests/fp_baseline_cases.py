"""Failure discrimination for the P1 gate; no SSH, Qdrant or model calls."""
import json
import copy
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/fp'))
from baseline_io import BASE, compare, dump, fingerprint, load, resolve, verify_artifact, verify_source
from validate_contracts import Contracts
from check_baseline import (check, validate_release_pins, verify_bppc_target,
                            verify_mac_target, verify_pi_copies)
from capture_baseline import capture_source
from baseline_runtime import verify_runtime
from serving_amendment import approval_binding


class BaselineFailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts = Contracts()

    def test_every_schema_has_discriminating_positive_and_negative_fixtures(self):
        self.assertGreaterEqual(self.contracts.fixtures(), 300)

    def test_runtime_rejects_a_real_validator_version_change(self):
        with patch('baseline_runtime.importlib.metadata.version', return_value='4.26.0'):
            with self.assertRaisesRegex(ValueError, 'validator.jsonschema'):
                verify_runtime()

    def test_runtime_rejects_missing_format_checkers(self):
        from jsonschema import FormatChecker
        for name in ['date', 'date-time', 'uri']:
            with self.subTest(format=name), patch.dict(FormatChecker.checkers):
                del FormatChecker.checkers[name]
                with self.assertRaisesRegex(ValueError, 'validator.format.' + name):
                    verify_runtime()

    def test_runtime_rejects_a_real_python_version_change(self):
        with patch('baseline_runtime.platform.python_version', return_value='3.11.6'):
            with self.assertRaisesRegex(ValueError, 'validator.python'):
                verify_runtime()

    def test_pinned_launcher_supports_python_module_arguments(self):
        path = BASE / 'bppc-machine-amendment-2026-10-15.json'
        launcher = Path(__file__).resolve().parents[1] / 'scripts/fp/run-python.sh'
        result = subprocess.run(['bash', str(launcher), '-m', 'json.tool', str(path)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout.split('\n', 1)[1]), load(path))

    def test_invalid_date_time_still_fails_schema_validation(self):
        cases = load(BASE / 'fixtures/v1/stale-flag-payload.json')
        case = next(item for item in cases['invalid'] if item['name'] == 'invalid date')
        with self.assertRaisesRegex(ValueError, 'date-time'):
            self.contracts.validate('stale-flag-payload', case['value'])

    def test_changed_file_and_missing_file_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'source.txt'
            path.write_text('frozen input')
            locations = {'roots': {'test': folder}}
            artifact = {'location': {'backend': 'test', 'path': 'source.txt'}, **fingerprint(path)}
            verify_artifact(artifact, locations)
            path.write_text('changed input')
            with self.assertRaisesRegex(ValueError, 'missing/changed'):
                verify_artifact(artifact, locations)
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                verify_artifact(artifact, locations)

    def test_remote_control_hash_changed_or_missing_fails(self):
        record = {'location': {'backend': 'bppc', 'path': 'gate/v10-hard.jsonl'}, 'sha256': 'a' * 64, 'bytes': 10}
        remote = {'files': {'gate/v10-hard.jsonl': {'sha256': 'a' * 64, 'bytes': 10}}}
        verify_artifact(record, {}, remote)
        remote['files']['gate/v10-hard.jsonl']['sha256'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'missing/changed'):
            verify_artifact(record, {}, remote)
        remote['files'].clear()
        with self.assertRaisesRegex(ValueError, 'missing/changed'):
            verify_artifact(record, {}, remote)

    def test_point_membership_drift_fails(self):
        with self.assertRaisesRegex(ValueError, 'membership'):
            compare('membership', 330778, 330777)

    def test_paths_and_symlinks_cannot_escape_artifact_root(self):
        with tempfile.TemporaryDirectory() as folder:
            locations = {'roots': {'test': folder}}
            for path in ['/etc/passwd', '../outside']:
                with self.assertRaises(ValueError):
                    resolve({'backend': 'test', 'path': path}, locations)
            (Path(folder) / 'escape').symlink_to('/etc')
            with self.assertRaises(ValueError):
                resolve({'backend': 'test', 'path': 'escape/passwd'}, locations)

    def test_incomplete_scope_cannot_be_declared_absent(self):
        response = json.loads((BASE / 'fixtures/v1/response.coverage.json').read_text())['valid'][0]['value']
        response['data']['conclusion'] = 'no-indexed-evidence-in-scope'
        response['data']['certificate']['processing']['state'] = 'failed'
        with self.assertRaisesRegex(ValueError, 'incomplete scope'):
            self.contracts.validate('response.coverage', response)
        response['data']['conclusion'] = 'unknown'
        self.contracts.validate('response.coverage', response)

    def test_real_evidence_bytes_cannot_change_under_same_hash(self):
        evidence = json.loads((BASE / 'fixtures/v1/evidence-read.json').read_text())['valid'][0]['value']
        self.contracts.validate('evidence-read', evidence)
        evidence['content'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'content hash differs'):
            self.contracts.validate('evidence-read', evidence)

    def test_missing_or_unreachable_schema_ref_fails_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            (base / 'contracts/v1').mkdir(parents=True)
            schema = {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': 'urn:synthetic:test',
                      'anyOf': [{'type': 'string'}, {'$ref': 'urn:missing:schema'}]}
            (base / 'contracts/v1/test.json').write_text(json.dumps(schema))
            with self.assertRaises(Exception):
                Contracts(base)

    def test_release_cannot_claim_tested_without_installation_receipt(self):
        release = json.loads((BASE / 'fixtures/v1/tested-release.json').read_text())['valid'][0]['value']
        release['deployment_state'] = 'released'
        with self.assertRaisesRegex(ValueError, 'tested/released'):
            self.contracts.validate('tested-release', release)

    def test_legacy_signatures_and_payload_type_are_preserved(self):
        get_chapter = self.contracts.schemas['request.get_chapter']['properties']['arguments']
        self.assertEqual(get_chapter['required'], ['book', 'chapter'])
        self.assertEqual(get_chapter['properties']['chapter'], {'anyOf': [{'type': 'string'}, {'type': 'integer'}]})
        read_chunk = self.contracts.schemas['request.read_chunk']['properties']['arguments']
        self.assertEqual(read_chunk['properties']['window']['default'], 1)
        response = json.loads((BASE / 'fixtures/v1/response.get_chapter.json').read_text())['valid'][0]['value']
        self.contracts.validate('response.get_chapter', response)
        response['legacy_output'] = {'text': 'shape changed'}
        with self.assertRaises(ValueError):
            self.contracts.validate('response.get_chapter', response)

    def test_legacy_wrapper_operation_must_match_arguments(self):
        request = json.loads((BASE / 'fixtures/v1/request.legacy_read.json').read_text())['valid'][0]['value']
        request['arguments'] = {'chunk_id': 'synthetic-child'}
        with self.assertRaises(ValueError):
            self.contracts.validate('request.legacy_read', request)

    def test_required_units_cannot_have_zero_processing_for_absence(self):
        response = json.loads((BASE / 'fixtures/v1/response.coverage.json').read_text())['valid'][0]['value']
        response['data']['conclusion'] = 'no-indexed-evidence-in-scope'
        for key in ['expected', 'attempted', 'completed']:
            response['data']['certificate']['processing'][key]['value'] = 0
        with self.assertRaisesRegex(ValueError, 'every required unit'):
            self.contracts.validate('response.coverage', response)

    def test_evidence_metadata_cannot_point_at_other_source_or_text(self):
        original = json.loads((BASE / 'fixtures/v1/evidence-read.json').read_text())['valid'][0]['value']
        for key, replacement in [('source_id', 'other-source'), ('source_revision', 'other-revision'), ('returned_text_hash', 'f' * 64)]:
            changed = copy.deepcopy(original)
            changed['metadata']['sources'][0][key] = replacement
            with self.assertRaisesRegex(ValueError, 'same source revision'):
                self.contracts.validate('evidence-read', changed)

    def test_verified_installation_requires_a_receipt(self):
        release = json.loads((BASE / 'fixtures/v1/tested-release.json').read_text())['valid'][0]['value']
        release['installation_matrix'][0]['verdict'] = 'verified'
        with self.assertRaisesRegex(ValueError, 'row requires a receipt'):
            self.contracts.validate('tested-release', release)

    def test_release_routing_model_and_component_claims_match_baseline(self):
        baseline = json.loads((BASE / 'baseline.json').read_text())
        original = json.loads((BASE / 'tested-release-v10.json').read_text())
        validate_release_pins(baseline, original)
        mutations = [
            ('routing', lambda value: value['routing'].update(physical_collection='wrong-collection')),
            ('model', lambda value: value['models'][0].update(revision='f' * 40)),
            ('component', lambda value: value['components'][0].update(revision='f' * 40)),
            ('data part', lambda value: value['data_parts'].pop()),
        ]
        for label, mutate in mutations:
            changed = copy.deepcopy(original)
            mutate(changed)
            with self.assertRaisesRegex(ValueError, label):
                validate_release_pins(baseline, changed)

    def test_release_cannot_hide_unfinished_installation_by_clearing_pending_gates(self):
        release = json.loads((BASE / 'tested-release-v10.json').read_text())
        release['deployment_state'] = 'released'
        release['pending_gates'] = []
        with self.assertRaisesRegex(ValueError, 'unfinished installation'):
            self.contracts.validate('tested-release', release)

    def test_unknown_schema_version_is_not_guessed(self):
        request = json.loads((BASE / 'fixtures/v1/request.source_read.json').read_text())['valid'][0]['value']
        request['schema_version'] = 'mind-tool-request/v99'
        with self.assertRaises(ValueError):
            self.contracts.validate('request.source_read', request)


class FrozenSourceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.locations = {'roots': {'repo': str(self.root), 'main-checkout': str(self.root),
                                    'pi-mind': str(self.root)}}
        self.git('init', '-q')
        self.git('config', 'user.name', 'Baseline test')
        self.git('config', 'user.email', 'baseline@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        self.path = self.root / 'knowledge_base/config.py'
        self.path.parent.mkdir()
        self.path.write_text('DIMENSION = 1024\n')
        self.git('add', 'knowledge_base/config.py')
        self.git('-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Frozen baseline')
        self.commit = self.git('rev-parse', 'HEAD')
        self.revisions = {'repo': self.commit, 'pi-mind': self.commit}
        self.record = {'location': {'backend': 'repo', 'path': 'knowledge_base/config.py'},
                       **fingerprint(self.path), 'verification': 'git',
                       'git_blob': self.git('rev-parse', 'HEAD:knowledge_base/config.py')}

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, stderr=subprocess.PIPE,
                                       text=True).strip()

    def verify(self, record=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            verify_source(record or self.record, self.locations, self.revisions)
        return output.getvalue()

    def test_modified_working_tree_config_passes_with_information(self):
        self.path.write_text('DIMENSION = 768\n')
        self.assertIn('INFO: repo:knowledge_base/config.py: changed since baseline', self.verify())

    def test_later_commit_and_missing_working_tree_source_do_not_change_pin(self):
        self.path.write_text('DIMENSION = 768\n')
        self.git('add', 'knowledge_base/config.py')
        self.git('-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Future change')
        self.assertIn('changed since baseline', self.verify())
        self.path.unlink()
        self.assertIn('changed since baseline', self.verify())

    def test_changed_blob_id_sha256_or_byte_count_in_record_fails(self):
        for field, value in [('git_blob', 'f' * 40), ('sha256', 'f' * 64), ('bytes', 1)]:
            with self.subTest(field=field):
                changed = {**self.record, field: value}
                with self.assertRaisesRegex(ValueError, 'changed baseline'):
                    self.verify(changed)

    def test_missing_baseline_commit_fails(self):
        self.revisions['repo'] = 'f' * 40
        with self.assertRaisesRegex(ValueError, 'missing Git'):
            self.verify()

    def test_capture_missing_git_blob_or_commit_cannot_become_observation(self):
        self.assertEqual(capture_source('repo', 'knowledge_base/config.py', self.locations, self.revisions),
                         self.record)
        blob = self.record['git_blob']
        (self.root / '.git/objects' / blob[:2] / blob[2:]).unlink()
        with self.assertRaisesRegex(ValueError, 'missing Git'):
            capture_source('repo', 'knowledge_base/config.py', self.locations, self.revisions)
        self.revisions['repo'] = 'f' * 40
        with self.assertRaisesRegex(ValueError, 'missing Git'):
            capture_source('repo', 'knowledge_base/config.py', self.locations, self.revisions)

    def test_capture_observation_requires_path_absent_from_git_tree(self):
        path = self.root / 'draft.md'
        path.write_text('What P1 read\n')
        record = capture_source('repo', path.name, self.locations, self.revisions)
        self.assertEqual(record['verification'], 'observation')
        self.assertEqual({k: record[k] for k in ['sha256', 'bytes']}, fingerprint(path))
        path.write_text('Future draft\n')
        self.assertIn('changed since baseline', self.verify(record))

    def test_edited_uncommitted_document_is_informational_and_keeps_observation(self):
        path = self.root / 'design-spec.md'
        path.write_text('What P1 read\n')
        record = {'location': {'backend': 'main-checkout', 'path': path.name},
                  **fingerprint(path), 'verification': 'observation'}
        frozen = copy.deepcopy(record)
        self.assertIn('unchanged', self.verify(record))
        path.write_text('Next design revision\n')
        self.assertIn('INFO: main-checkout:design-spec.md: changed since baseline', self.verify(record))
        path.unlink()
        self.assertIn('changed since baseline', self.verify(record))
        self.assertEqual(record, frozen)

    def test_uncommitted_repo_document_is_also_informational(self):
        path = self.root / 'draft.md'
        path.write_text('What P1 read\n')
        record = {'location': {'backend': 'repo', 'path': path.name},
                  **fingerprint(path), 'verification': 'observation'}
        path.write_text('Next draft\n')
        self.assertIn('changed since baseline', self.verify(record))

    def test_changed_release_manifest_or_part_fails(self):
        for name in ['dist/release/manifest.json', 'dist/release/kb-core.part00']:
            with self.subTest(path=name):
                path = self.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'frozen release bytes')
                record = {'location': {'backend': 'main-checkout', 'path': name},
                          **fingerprint(path), 'verification': 'strict'}
                self.verify(record)
                path.write_bytes(b'changed release bytes')
                with self.assertRaisesRegex(ValueError, 'missing/changed'):
                    self.verify(record)

    def test_pi_mind_drift_passes_but_copies_must_match_pinned_commit(self):
        base = self.root / 'baseline'
        records = []
        for upstream, local in [('schemas', 'contracts/v1'), ('test/fixtures', 'fixtures/v1')]:
            name = f'packages/contracts/{upstream}/memory-record.json'
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{"frozen":true}\n')
            target = base / local / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
            records.append({'location': {'backend': 'pi-mind', 'path': name},
                            **fingerprint(path), 'verification': 'git'})
            self.git('add', name)
        self.git('-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'W1 contracts')
        self.revisions['pi-mind'] = self.git('rev-parse', 'HEAD')
        for record in records:
            name = record['location']['path']
            record['git_blob'] = self.git('rev-parse', f'HEAD:{name}')
            (self.root / name).write_text('{"future":true}\n')
            self.assertIn('INFO: pi-mind:', self.verify(record))
        schemas = {'memory-record': {'$id': 'urn:pi-mind:memory-record@1'}}
        baseline = {'local_sources': records, 'source_revisions': self.revisions}
        with patch('check_baseline.BASE', base):
            verify_pi_copies(schemas, baseline, self.locations)
            (base / 'contracts/v1/memory-record.json').write_text('{"future":true}\n')
            with self.assertRaisesRegex(ValueError, 'pi-mind copy equality'):
                verify_pi_copies(schemas, baseline, self.locations)

    def test_full_checker_uses_source_policies_for_release_references_too(self):
        base = self.root / 'data/baseline'
        baseline = load(BASE / 'baseline.json')
        release = load(BASE / 'tested-release-v10.json')
        path = self.root / 'design-spec.md'
        path.write_text('What P1 read\n')
        document = {'location': {'backend': 'main-checkout', 'path': path.name},
                    **fingerprint(path), 'verification': 'observation'}
        part_path = self.root / 'dist/release/kb-core.part00'
        part_path.parent.mkdir(parents=True)
        part_path.write_bytes(b'frozen release')
        part = {'location': {'backend': 'main-checkout', 'path': 'dist/release/kb-core.part00'},
                **fingerprint(part_path)}
        baseline['source_revisions'] = self.revisions
        baseline['server']['revision'] = self.commit
        baseline['local_sources'] = [self.record, document, part]
        baseline['component_pins'] = [{'role': 'knowledge-base', 'revision': self.commit,
                                      'file_pins': [{k: self.record[k] for k in ['location', 'sha256', 'bytes']}]},
                                     {'role': 'harness', 'revision': self.commit, 'file_pins': []}]
        release = {k: release[k] for k in ['routing', 'models', 'deployment_state']}
        release.update(components=baseline['component_pins'], data_parts=[part])
        dump(base / 'baseline.json', baseline)
        dump(base / 'contracts-lock.json', {'artifacts': []})
        for field, name in [('baseline', 'baseline.json'), ('contract_inventory', 'contracts-lock.json')]:
            release[field] = {'location': {'backend': 'repo', 'path': 'data/baseline/' + name},
                              **fingerprint(base / name)}
        dump(base / 'tested-release-v10.json', release)
        dump(base / 'locations.json', {**self.locations, 'mac_qdrant_url': 'http://test.invalid',
                                       'bppc_hosts': ['test.invalid']})
        dump(base / 'redirects-m1c.json', {})
        observed_mac = copy.deepcopy(baseline['mac'])
        observed_mac['aliases'][0]['collection_name'] = 'developer_knowledge_v11'
        self.path.write_text('DIMENSION = 768\n')
        path.write_text('Future design\n')
        output = io.StringIO()
        with patch('check_baseline.BASE', base), patch('check_baseline.ROOT', self.root), \
             patch('check_baseline.Contracts') as contracts, patch('check_baseline.verify_approval'), \
             patch('check_baseline.local_target', return_value=observed_mac), \
             patch('check_baseline.remote_target', return_value=baseline['remote']), \
             contextlib.redirect_stdout(output):
            contracts.return_value.schemas = {}
            contracts.return_value.fixtures.return_value = 0
            check()
            part_path.write_bytes(b'changed release')
            with self.assertRaisesRegex(ValueError, 'missing/changed artifact'):
                check()
        for line in ['repo:knowledge_base/config.py: changed since baseline',
                     'main-checkout:design-spec.md: changed since baseline',
                     'alias now -> developer_knowledge_v11', 'PASS: FP P1 mechanical baseline gate']:
            self.assertIn(line, output.getvalue())


class PhysicalCollectionTests(unittest.TestCase):
    def setUp(self):
        self.expected = {'aliases': [{'alias_name': 'developer_knowledge',
                                     'collection_name': 'developer_knowledge_v10'}],
                         'collection': {'name': 'developer_knowledge_v10', 'points_count': 330778,
                                        'config': {'params': {'vectors': {'size': 1024, 'distance': 'Cosine'},
                                                              'sparse_vectors': {'bm25': {'modifier': 'idf'}}}}},
                         'machine': {'qdrant': {'version': '1.18.2'}}}

    def test_alias_moves_or_disappears_without_failing_physical_collection_gate(self):
        for aliases, target in [([{'alias_name': 'developer_knowledge',
                                  'collection_name': 'developer_knowledge_v11'}], 'developer_knowledge_v11'),
                                ([], '(absent)')]:
            observed = {**self.expected, 'aliases': aliases}
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                verify_mac_target(self.expected, observed)
            self.assertIn(f'INFO: alias now -> {target}', output.getvalue())

    def test_missing_or_changed_v10_fails(self):
        for mutation in [lambda value: value.pop('collection'),
                         lambda value: value['collection'].update(points_count=330777),
                         lambda value: value['collection']['config']['params']['vectors'].update(size=768),
                         lambda value: value['collection']['config']['params']['vectors'].update(distance='Dot'),
                         lambda value: value['collection']['config']['params']['sparse_vectors']['bm25'].update(modifier=None)]:
            observed = copy.deepcopy(self.expected)
            mutation(observed)
            with self.assertRaisesRegex(ValueError, 'physical collection'):
                verify_mac_target(self.expected, observed)


class ServingAmendmentTests(unittest.TestCase):
    def setUp(self):
        self.expected = load(BASE / 'baseline.json')['mac']
        self.observed = copy.deepcopy(self.expected)
        self.observed['machine']['query_packages'].update(transformers='5.19.0', torchvision='0.29.1')
        self.observed['aliases'][0]['collection_name'] = 'developer_knowledge_v11'
        self.amendment = load(BASE / 'serving-stack-amendment-2026-10-16.json')

    def verify(self, amendment):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            verify_mac_target(self.expected, self.observed, amendment)
        return output.getvalue()

    def test_approved_exact_serving_change_passes_and_reports_amendment(self):
        frozen = copy.deepcopy(self.expected)
        output = self.verify(self.amendment)
        self.assertIn('alias now -> developer_knowledge_v11', output)
        self.assertIn('amendment approved by Gary on 2026-10-16', output)
        self.assertIn('5.17.0 -> 5.19.0', output)
        self.assertEqual(self.expected, frozen)

    def test_serving_change_without_an_amendment_fails(self):
        with self.assertRaisesRegex(ValueError, 'Mac versions'):
            self.verify(None)

    def test_unapproved_serving_change_fails(self):
        self.amendment['approved_by'] = 'pending'
        with self.assertRaisesRegex(ValueError, 'amendment approval'):
            self.verify(self.amendment)

    def test_one_different_observed_version_fails(self):
        for package in ['transformers', 'torchvision']:
            with self.subTest(package=package):
                saved = self.observed['machine']['query_packages'][package]
                self.observed['machine']['query_packages'][package] = '99.0.1'
                with self.assertRaisesRegex(ValueError, 'Mac versions.query_packages.' + package):
                    self.verify(self.amendment)
                self.observed['machine']['query_packages'][package] = saved

    def test_broken_approval_binding_fails(self):
        self.amendment['approval_binding_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'amendment approval binding'):
            self.verify(self.amendment)

    def test_rebound_unapproved_version_still_fails_committed_lock_binding(self):
        self.amendment['changes']['transformers']['after'] = '5.19.1'
        self.amendment['approval_binding_sha256'] = approval_binding(self.amendment)
        with self.assertRaisesRegex(ValueError, 'amendment approved version transformers'):
            self.verify(self.amendment)

    def test_changed_gate_hash_or_approval_commit_fails_even_when_rebound(self):
        for field in ['revision', 'gate hash']:
            with self.subTest(field=field):
                record = copy.deepcopy(self.amendment)
                if field == 'revision':
                    record['approval_source']['revision'] = '0' * 40
                else:
                    record['approval_source']['artifacts'][0]['sha256'] = '0' * 64
                record['approval_binding_sha256'] = approval_binding(record)
                with self.assertRaisesRegex(ValueError, 'amendment approval (revision|source)'):
                    self.verify(record)

    def test_missing_extra_and_unrelated_package_changes_fail(self):
        for package, replacement in [('torch', '99.0.1'), ('torchvision', None), ('extra-package', '1.0')]:
            with self.subTest(package=package):
                observed = copy.deepcopy(self.observed)
                if replacement is None:
                    del observed['machine']['query_packages'][package]
                else:
                    observed['machine']['query_packages'][package] = replacement
                with self.assertRaisesRegex(ValueError, 'Mac versions.query_packages.' + package):
                    verify_mac_target(self.expected, observed, self.amendment)

    def test_partial_switch_fails(self):
        self.observed['machine']['query_packages']['transformers'] = '5.17.0'
        with self.assertRaisesRegex(ValueError, 'Mac versions.query_packages.transformers'):
            self.verify(self.amendment)

    def test_unchanged_baseline_also_passes_with_the_recorded_amendment(self):
        self.observed = copy.deepcopy(self.expected)
        self.verify(self.amendment)

    def test_other_machine_or_collection_changes_still_fail(self):
        for section, field, value in [('machine', 'kernel', 'future-kernel'),
                                      ('collection', 'points_count', 330777)]:
            with self.subTest(field=field):
                saved = self.observed[section][field]
                self.observed[section][field] = value
                with self.assertRaisesRegex(ValueError, 'Mac (versions|physical collection)'):
                    self.verify(self.amendment)
                self.observed[section][field] = saved


class MacAmendmentTests(unittest.TestCase):
    def setUp(self):
        self.expected = load(BASE / 'baseline.json')['mac']
        self.observed = copy.deepcopy(self.expected)
        self.observed['machine'].update(kernel='27.0.0', os='macOS 27.0.1')
        self.amendment = load(BASE / 'mac-machine-amendment-2026-10-19.json')

    def verify(self, amendment):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            verify_mac_target(self.expected, self.observed, mac_amendment=amendment)
        return output.getvalue()

    def test_approved_exact_mac_update_passes_without_mutating_inputs(self):
        frozen, observed = copy.deepcopy(self.expected), copy.deepcopy(self.observed)
        output = self.verify(self.amendment)
        self.assertIn("INFO: Mac machine amendment approved by coordinator on Gary's delegation (2026-10-19)", output)
        self.assertIn('macOS 27 update', output)
        self.assertIn('kernel: 25.6.0 -> 27.0.0', output)
        self.assertIn('os: macOS 26.6.2 -> macOS 27.0.1', output)
        self.assertEqual(self.expected, frozen)
        self.assertEqual(self.observed, observed)

    def test_mac_update_without_amendment_fails(self):
        with self.assertRaisesRegex(ValueError, 'Mac versions.kernel'):
            self.verify(None)

    def test_unchanged_mac_passes_with_or_without_amendment(self):
        self.observed = copy.deepcopy(self.expected)
        self.verify(None)
        self.verify(self.amendment)

    def test_other_observed_mac_values_and_partial_updates_fail(self):
        for field, value in [('kernel', '27.0.1'), ('os', 'macOS 27.0.2'),
                             ('kernel', self.expected['machine']['kernel']),
                             ('os', self.expected['machine']['os'])]:
            with self.subTest(field=field, value=value):
                saved = self.observed['machine'][field]
                self.observed['machine'][field] = value
                with self.assertRaisesRegex(ValueError, 'Mac versions.' + field):
                    self.verify(self.amendment)
                self.observed['machine'][field] = saved

    def test_unlisted_mac_machine_and_collection_changes_fail(self):
        for section, field, value in [('machine', 'architecture', 'x86_64'),
                                      ('machine', 'python_query', 'Python 3.11.6'),
                                      ('machine', 'build', '26A435'),
                                      ('collection', 'points_count', 330777)]:
            with self.subTest(field=field):
                self.observed = copy.deepcopy(self.expected)
                self.observed['machine'].update(kernel='27.0.0', os='macOS 27.0.1')
                self.observed[section][field] = value
                with self.assertRaisesRegex(ValueError, 'Mac (versions|physical collection)'):
                    self.verify(self.amendment)

    def test_broken_mac_approval_binding_fails_even_for_unchanged_observation(self):
        self.amendment['approval_binding_sha256'] = '0' * 64
        for observed in [self.observed, copy.deepcopy(self.expected)]:
            with self.subTest(unchanged=observed == self.expected):
                self.observed = observed
                with self.assertRaisesRegex(ValueError, 'Mac amendment approval binding'):
                    self.verify(self.amendment)

    def test_changed_mac_approval_fails_even_when_rebound(self):
        for field, value in [('approved_by', 'pending'), ('approved_at', '2026-10-20'),
                             ('schema_version', 'fp/mac-machine-amendment@99'),
                             ('reason', 'unapproved update')]:
            with self.subTest(field=field):
                record = copy.deepcopy(self.amendment)
                record[field] = value
                record['approval_binding_sha256'] = approval_binding(record)
                with self.assertRaisesRegex(ValueError, 'Mac amendment'):
                    self.verify(record)

    def test_different_recorded_mac_before_or_after_fails_even_when_rebound(self):
        for name, value in [('kernel', '27.0.1'), ('os', 'macOS 27.0.2')]:
            for field in ['before', 'after']:
                with self.subTest(name=name, field=field):
                    record = copy.deepcopy(self.amendment)
                    record['changes'][name][field] = value
                    record['approval_binding_sha256'] = approval_binding(record)
                    self.observed['machine'][name] = record['changes'][name]['after']
                    with self.assertRaisesRegex(ValueError, 'Mac amendment change scope'):
                        self.verify(record)

    def test_missing_or_extra_mac_amended_fields_fail_even_when_rebound(self):
        changesets = [{}, {**self.amendment['changes'], 'architecture': {'before': 'arm64', 'after': 'x86_64'}}]
        changesets.extend({name: change for name, change in self.amendment['changes'].items() if name != missing}
                          for missing in ['kernel', 'os'])
        for changes in changesets:
            with self.subTest(changes=changes):
                record = copy.deepcopy(self.amendment)
                record['changes'] = changes
                record['approval_binding_sha256'] = approval_binding(record)
                with self.assertRaisesRegex(ValueError, 'Mac amendment change scope'):
                    self.verify(record)

    def test_mac_amendment_requires_original_frozen_values(self):
        for field in ['kernel', 'os']:
            with self.subTest(field=field):
                saved = self.expected['machine'][field]
                self.expected['machine'][field] = 'unapproved original'
                with self.assertRaisesRegex(ValueError, 'Mac amendment original ' + field):
                    self.verify(self.amendment)
                self.expected['machine'][field] = saved

    def test_mac_amendment_wrong_baseline_fails_even_when_rebound(self):
        for field, value in [('sha256', '0' * 64), ('bytes', 0),
                             ('location', {'backend': 'repo', 'path': 'other.json'})]:
            with self.subTest(field=field):
                record = copy.deepcopy(self.amendment)
                record['baseline'][field] = value
                record['approval_binding_sha256'] = approval_binding(record)
                with self.assertRaisesRegex(ValueError, 'amendment (frozen baseline|baseline location)'):
                    self.verify(record)

    def test_mac_and_serving_amendments_compose_and_keep_other_packages_strict(self):
        serving = load(BASE / 'serving-stack-amendment-2026-10-16.json')
        self.observed['machine']['query_packages'].update(transformers='5.19.0', torchvision='0.29.1')
        verify_mac_target(self.expected, self.observed, serving, self.amendment)
        self.observed['machine']['query_packages']['torch'] = '99.0.1'
        with self.assertRaisesRegex(ValueError, 'Mac versions.query_packages.torch'):
            verify_mac_target(self.expected, self.observed, serving, self.amendment)


class BppcAmendmentTests(unittest.TestCase):
    def setUp(self):
        self.expected = load(BASE / 'baseline.json')['remote']
        self.observed = copy.deepcopy(self.expected)
        self.observed['machine'].update(kernel='7.0.0-38-generic', os='Ubuntu 24.04.5 LTS')
        self.amendment = load(BASE / 'bppc-machine-amendment-2026-10-15.json')

    def verify(self, amendment):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            verify_bppc_target(self.expected, self.observed, amendment)
        return output.getvalue()

    def test_approved_exact_bppc_kernel_change_passes_without_mutating_inputs(self):
        frozen, observed = copy.deepcopy(self.expected), copy.deepcopy(self.observed)
        output = self.verify(self.amendment)
        self.assertIn('bppc machine amendment approved by Gary on 2026-10-15', output)
        self.assertIn('OS update reboot', output)
        self.assertIn('7.0.0-28-generic -> 7.0.0-38-generic', output)
        self.assertIn('os: Ubuntu 24.04.4 LTS -> Ubuntu 24.04.5 LTS', output)
        self.assertEqual(self.expected, frozen)
        self.assertEqual(self.observed, observed)

    def test_bppc_kernel_change_without_amendment_fails(self):
        with self.assertRaisesRegex(ValueError, r'bppc frozen.*machine.kernel'):
            self.verify(None)

    def test_bppc_os_change_without_amendment_entry_fails(self):
        record = copy.deepcopy(self.amendment)
        record['changes'].pop('os', None)
        record['approval_binding_sha256'] = approval_binding(record)
        with self.assertRaisesRegex(ValueError, 'bppc amendment change scope'):
            self.verify(record)

    def test_unchanged_bppc_passes_with_or_without_amendment(self):
        self.observed = copy.deepcopy(self.expected)
        self.verify(None)
        self.verify(self.amendment)

    def test_other_observed_bppc_kernel_fails(self):
        for field, value in [('kernel', '7.0.0-39-generic'), ('os', 'Ubuntu 24.04.6 LTS'),
                             ('kernel', self.expected['machine']['kernel']),
                             ('os', self.expected['machine']['os'])]:
            with self.subTest(field=field, value=value):
                saved = self.observed['machine'][field]
                self.observed['machine'][field] = value
                with self.assertRaisesRegex(ValueError, r'bppc frozen.*machine\.' + field):
                    self.verify(self.amendment)
                self.observed['machine'][field] = saved

    def test_changed_bppc_approval_fails_even_when_rebound(self):
        for field, value in [('approved_by', 'pending'), ('approved_at', '2026-10-16'),
                             ('schema_version', 'fp/bppc-machine-amendment@99'),
                             ('reason', 'unapproved reboot')]:
            with self.subTest(field=field):
                record = copy.deepcopy(self.amendment)
                record[field] = value
                record['approval_binding_sha256'] = approval_binding(record)
                with self.assertRaisesRegex(ValueError, 'bppc amendment'):
                    self.verify(record)

    def test_broken_bppc_approval_binding_fails(self):
        self.amendment['approval_binding_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'bppc amendment approval binding'):
            self.verify(self.amendment)

    def test_different_recorded_bppc_from_or_to_fails_even_when_rebound(self):
        for name, value in [('kernel', '7.0.0-39-generic'), ('os', 'Ubuntu 24.04.6 LTS')]:
            for field in ['before', 'after']:
                with self.subTest(name=name, field=field):
                    record = copy.deepcopy(self.amendment)
                    record['changes'][name][field] = value
                    record['approval_binding_sha256'] = approval_binding(record)
                    observed = copy.deepcopy(self.observed)
                    observed['machine'][name] = record['changes'][name]['after']
                    with self.assertRaisesRegex(ValueError, 'bppc amendment change scope'):
                        verify_bppc_target(self.expected, observed, record)

    def test_missing_or_extra_bppc_amended_fields_fail_even_when_rebound(self):
        changesets = [{}, {**self.amendment['changes'], 'architecture': {'before': 'old', 'after': 'new'}}]
        changesets.extend({name: change for name, change in self.amendment['changes'].items() if name != missing}
                          for missing in ['kernel', 'os'])
        for changes in changesets:
            with self.subTest(changes=changes):
                record = copy.deepcopy(self.amendment)
                record['changes'] = changes
                record['approval_binding_sha256'] = approval_binding(record)
                with self.assertRaisesRegex(ValueError, 'bppc amendment change scope'):
                    self.verify(record)

    def test_bppc_amendment_requires_original_frozen_kernel(self):
        for field in ['kernel', 'os']:
            with self.subTest(field=field):
                saved = self.expected['machine'][field]
                self.expected['machine'][field] = 'unapproved original'
                with self.assertRaisesRegex(ValueError, 'bppc amendment original ' + field):
                    self.verify(self.amendment)
                self.expected['machine'][field] = saved

    def test_bppc_amendment_wrong_baseline_fails_even_when_rebound(self):
        for field, value in [('sha256', '0' * 64), ('bytes', 0),
                             ('location', {'backend': 'bppc', 'path': 'other.json'})]:
            with self.subTest(field=field):
                record = copy.deepcopy(self.amendment)
                record['baseline'][field] = value
                record['approval_binding_sha256'] = approval_binding(record)
                with self.assertRaisesRegex(ValueError, 'amendment (frozen baseline|baseline location)'):
                    self.verify(record)

    def test_every_other_bppc_evidence_leaf_stays_strict(self):
        def leaves(value, path=()):
            if isinstance(value, (dict, list)):
                items = value.items() if isinstance(value, dict) else enumerate(value)
                for key, child in items:
                    yield from leaves(child, path + (key,))
            else:
                yield path

        paths = [path for path in leaves(self.expected) if path not in [('machine', 'kernel'), ('machine', 'os')]]
        self.assertGreater(len(paths), 1000)
        for path in paths:
            with self.subTest(path=path):
                parent = self.observed
                for key in path[:-1]:
                    parent = parent[key]
                saved = parent[path[-1]]
                parent[path[-1]] = None if saved is not None else 'unexpected'
                with self.assertRaisesRegex(ValueError, 'bppc frozen'):
                    self.verify(self.amendment)
                parent[path[-1]] = saved

    def test_missing_or_extra_bppc_evidence_still_fails(self):
        for section in [None, 'machine', 'files', 'models', 'collection', 'membership', 'controls', 'redirect']:
            for action in ['missing', 'extra']:
                with self.subTest(section=section, action=action):
                    self.observed = copy.deepcopy(self.expected)
                    self.observed['machine'].update(kernel='7.0.0-38-generic', os='Ubuntu 24.04.5 LTS')
                    parent = self.observed if section is None else self.observed[section]
                    if action == 'missing':
                        del parent[next(iter(parent))]
                    else:
                        parent['unexpected'] = 'extra evidence'
                    with self.assertRaisesRegex(ValueError, 'bppc frozen'):
                        self.verify(self.amendment)

    def test_invalid_bppc_amendment_cannot_hide_behind_unchanged_observation(self):
        self.observed = copy.deepcopy(self.expected)
        self.amendment['approval_binding_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'bppc amendment approval binding'):
            self.verify(self.amendment)

    def test_full_checker_loads_all_amendments_and_keeps_remote_checks(self):
        mac = load(BASE / 'baseline.json')['mac']
        mac['machine'].update(kernel='27.0.0', os='macOS 27.0.1')
        mac['machine']['query_packages'].update(transformers='5.19.0', torchvision='0.29.1')
        mac['aliases'][0]['collection_name'] = 'developer_knowledge_v11'
        output = io.StringIO()
        # Only external reads are stubbed; comparison and amendment loading are real.
        with patch('check_baseline.verify_source'), patch('check_baseline.verify_artifact'), \
             patch('check_baseline.verify_approval'), patch('check_baseline.verify_pi_copies'), \
             patch('check_baseline.local_target', return_value=mac), \
             patch('check_baseline.remote_target', return_value=self.observed), \
             contextlib.redirect_stdout(output):
            check()
            self.observed['controls']['hard']['output_sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, r'bppc frozen.*controls.hard.output_sha256'):
                check()
        self.assertIn('serving-stack amendment approved by Gary on 2026-10-16', output.getvalue())
        self.assertIn('Mac machine amendment approved by coordinator', output.getvalue())
        self.assertIn('bppc machine amendment approved by Gary on 2026-10-15', output.getvalue())
        self.assertIn('PASS: FP P1 mechanical baseline gate', output.getvalue())


if __name__ == '__main__':
    unittest.main()
