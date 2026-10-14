"""Mandatory connected P1 gate. Read-only; no offline-success or re-freeze mode."""
import importlib.metadata
import os
import sys
from pathlib import Path

from baseline_io import BASE, ROOT, compare, fingerprint, load, local_target, remote_target, resolve, roots, release_models
from validate_contracts import Contracts


def artifact_refs(value):
    if isinstance(value, dict):
        if set(['location', 'sha256', 'bytes']).issubset(value):
            yield value
        for child in value.values():
            yield from artifact_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from artifact_refs(child)


def validate_release_pins(baseline, release):
    expected_routing = {
        'alias': 'developer_knowledge', 'physical_collection': baseline['mac']['collection']['name'],
        'embedding_space': 'jina-v5-1024-' + baseline['remote']['models']['jinaai/jina-embeddings-v5-text-small-retrieval']['revision'],
        'source_generation': baseline['remote']['membership']['sha256'],
    }
    compare('release routing', expected_routing, release['routing'])
    compare('release model profiles', release_models(baseline), release['models'])
    compare('release component pins', baseline['component_pins'], release['components'])
    expected_parts = [item for item in baseline['local_sources'] if item['location']['backend'] == 'main-checkout'
                      and item['location']['path'].startswith('dist/release/kb-')]
    compare('release data part membership', expected_parts, release['data_parts'])
    compare('P1 manifest deployment state', 'baseline-only', release['deployment_state'])


def verify_approval(locations):
    approval = load(BASE / 'approval-source.json')
    main = Path(roots(locations)['main-checkout'])
    decisions = (main / 'wiki/decisions.md').read_text()
    current = decisions.split(approval['decision_heading'], 1)[1].split('\n## ', 1)[0]
    compare('2026-10-14 approved decision excerpt', approval['decision_body'], current)
    lines = (main / 'wiki/log.md').read_text().splitlines()
    if not all(line in lines for line in approval['log_lines_241_242']):
        raise ValueError('referenced log lines 241-242 are missing/changed')


def check():
    locations = load(BASE / 'locations.json')
    baseline = load(BASE / 'baseline.json')
    release = load(BASE / 'tested-release-v10.json')
    lock = load(BASE / 'contracts-lock.json')
    endpoint = os.environ.get('FP_QDRANT_URL', locations['mac_qdrant_url'])
    hosts = [os.environ['FP_BPPC_HOST']] if os.environ.get('FP_BPPC_HOST') else locations['bppc_hosts']
    print(f'Inputs: {BASE}; roots={roots(locations)}; Mac Qdrant {endpoint}; bppc hosts={hosts}', flush=True)
    compare('validator.jsonschema', baseline['validator']['jsonschema'], importlib.metadata.version('jsonschema'))
    pack = Contracts()
    cases = pack.fixtures()
    pack.validate('tested-release', release)
    validate_release_pins(baseline, release)
    locked_schema_paths = {entry['location']['path'] for entry in lock['artifacts']
                           if entry['location']['path'].startswith('data/baseline/contracts/v1/')}
    actual_schema_paths = {str(path.relative_to(ROOT)) for path in (BASE / 'contracts/v1').glob('*.json')}
    compare('schema inventory', sorted(locked_schema_paths), sorted(actual_schema_paths))
    locked_fixture_paths = {entry['location']['path'] for entry in lock['artifacts']
                            if entry['location']['path'].startswith('data/baseline/fixtures/v1/')}
    actual_fixture_paths = {str(path.relative_to(ROOT)) for path in (BASE / 'fixtures/v1').glob('*.json')}
    compare('fixture inventory', sorted(locked_fixture_paths), sorted(actual_fixture_paths))
    seen = {}
    def verify(artifact, remote=None):
        location = artifact['location']
        key = (location['backend'], location['path'])
        if key not in seen:
            if key[0] == 'bppc':
                if remote is None:
                    raise ValueError('remote evidence required')
                actual = remote['files'].get(key[1])
            else:
                actual = fingerprint(resolve(location, locations))
            seen[key] = actual
        compare(f'artifact {key[0]}:{key[1]}', {k: artifact[k] for k in ['sha256', 'bytes']}, seen[key])
    for item in lock['artifacts']:
        verify(item)
    for name, schema in pack.schemas.items():
        if schema['$id'].startswith('urn:pi-mind:'):
            for source, local in [('schemas', 'contracts/v1'), ('test/fixtures', 'fixtures/v1')]:
                upstream = {'backend': 'pi-mind', 'path': f'packages/contracts/{source}/{name}.json'}
                compare(f'pi-mind copy equality: {name}/{source}', fingerprint(resolve(upstream, locations)), fingerprint(BASE / local / f'{name}.json'))
    verify(release['baseline'])
    verify(release['contract_inventory'])
    for item in baseline['local_sources']:
        verify(item)
    verify_approval(locations)
    print(f'PASS: {len(pack.schemas)} schemas, 32 tool pairs, {cases} fixtures; local source/release hashes', flush=True)
    observed_mac = local_target(locations)
    compare('Mac live alias/collection/versions', baseline['mac'], observed_mac)
    print('PASS: Mac developer_knowledge -> developer_knowledge_v10 (330778 points, 1024 dimensions)', flush=True)
    print('Reading bppc frozen payloads, sparse fingerprints, models and 438/199/30 controls (no model execution)...', flush=True)
    observed_remote = remote_target(locations)
    compare('bppc frozen evidence/collection/versions', baseline['remote'], observed_remote)
    for value in [release, load(BASE / 'redirects-m1c.json')]:
        for item in artifact_refs(value):
            verify(item, observed_remote)
    for name, count in [('hard', 438), ('easy', 199), ('sanity', 30)]:
        compare(f'{name} control population', count, observed_remote['controls'][name]['count'])
    print(f'PASS: {len(observed_remote["files"])} bppc file hashes; 330778 IDs/payloads/BM25, 328 sources; original labels and M1c redirect', flush=True)
    print('PASS: FP P1 mechanical baseline gate. Gary contract approval and P7 installation gates remain pending.', flush=True)


if __name__ == '__main__':
    try:
        check()
    except Exception as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(1)
