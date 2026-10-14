"""Failure discrimination for the P1 gate; no SSH, Qdrant or model calls."""
import json
import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/fp'))
from baseline_io import BASE, compare, fingerprint, resolve, verify_artifact
from validate_contracts import Contracts
from check_baseline import validate_release_pins


class BaselineFailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts = Contracts()

    def test_every_schema_has_discriminating_positive_and_negative_fixtures(self):
        self.assertGreaterEqual(self.contracts.fixtures(), 300)

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

    def test_alias_retarget_and_point_membership_drift_fail(self):
        expected = {'alias_name': 'developer_knowledge', 'collection_name': 'developer_knowledge_v10'}
        changed = {**expected, 'collection_name': 'gemma-candidate'}
        with self.assertRaisesRegex(ValueError, 'collection_name'):
            compare('live alias', expected, changed)
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


if __name__ == '__main__':
    unittest.main()
