"""Mandatory connected P1 gate. Read-only; no offline-success or re-freeze mode."""
import importlib.metadata
import os
import sys
from pathlib import Path

from baseline_io import (BASE, ROOT, compare, fingerprint, git_fingerprint, load, local_target,
                         remote_target, roots, release_models, verify_artifact, verify_source)
from validate_contracts import Contracts
from serving_amendment import (AMENDMENT_NAME, BPPC_AMENDMENT_NAME,
                               amended_bppc_machine, amended_machine)


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


def verify_pi_copies(schemas, baseline, locations):
    sources = {(item['location']['backend'], item['location']['path']): item
               for item in baseline['local_sources']}
    for name, schema in schemas.items():
        if schema['$id'].startswith('urn:pi-mind:'):
            for source, local in [('schemas', 'contracts/v1'), ('test/fixtures', 'fixtures/v1')]:
                path = f'packages/contracts/{source}/{name}.json'
                record = sources[('pi-mind', path)]
                compare(f'pi-mind imported source policy: {path}', 'git', record['verification'])
                frozen = git_fingerprint(record['location'], locations, baseline['source_revisions']['pi-mind'])
                compare(f'pi-mind copy equality: {name}/{source}',
                        {key: frozen[key] for key in ['sha256', 'bytes']},
                        fingerprint(BASE / local / f'{name}.json'))


def verify_mac_target(expected, observed, amendment=None):
    compare('Mac physical collection', expected['collection'], observed.get('collection'))
    targets = [item['collection_name'] for item in observed['aliases']
               if item['alias_name'] == 'developer_knowledge']
    print(f'INFO: alias now -> {", ".join(targets) if targets else "(absent)"}', flush=True)
    machine = expected['machine']
    if amendment is not None:
        machine = amended_machine(machine, amendment)
        changes = '; '.join(f'{name}: {change["before"] or "(not captured)"} -> {change["after"]}'
                            for name, change in sorted(amendment['changes'].items()))
        print(f'INFO: serving-stack amendment approved by {amendment["approved_by"]} on '
              f'{amendment["approved_at"]}; gate-v11 at {amendment["approval_source"]["revision"]}; '
              f'{changes}', flush=True)
    if observed['machine'] != expected['machine']:
        compare('Mac versions', machine, observed['machine'])


def verify_bppc_target(expected, observed, amendment=None):
    amended = expected
    if amendment is not None:
        amended = {**expected, 'machine': amended_bppc_machine(expected['machine'], amendment)}
        changes = '; '.join(f'{name}: {change["before"]} -> {change["after"]}'
                            for name, change in sorted(amendment['changes'].items()))
        print(f'INFO: bppc machine amendment approved by {amendment["approved_by"]} on '
              f'{amendment["approved_at"]}; {amendment["reason"]}; '
              f'{changes}', flush=True)
    if observed != expected:
        compare('bppc frozen evidence/collection/versions', amended, observed)


def check():
    locations = load(BASE / 'locations.json')
    baseline = load(BASE / 'baseline.json')
    release = load(BASE / 'tested-release-v10.json')
    lock = load(BASE / 'contracts-lock.json')
    endpoint = os.environ.get('FP_QDRANT_URL', locations['mac_qdrant_url'])
    hosts = [os.environ['FP_BPPC_HOST']] if os.environ.get('FP_BPPC_HOST') else locations['bppc_hosts']
    print(f'Inputs: {BASE}; roots={roots(locations)}; Mac Qdrant {endpoint}; bppc hosts={hosts}', flush=True)
    revisions = baseline['source_revisions']
    compare('baseline repo commit', baseline['server']['revision'], revisions['repo'])
    harness = next(item for item in baseline['component_pins'] if item['role'] == 'harness')
    compare('baseline pi-mind commit', harness['revision'], revisions['pi-mind'])
    print(f'Frozen source commits: repo={revisions["repo"]}; pi-mind={revisions["pi-mind"]}', flush=True)
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
    sources = {(item['location']['backend'], item['location']['path']): item
               for item in baseline['local_sources']}
    seen = {}
    def verify(artifact, remote=None):
        location = artifact['location']
        key = (location['backend'], location['path'])
        expected = {k: artifact[k] for k in ['sha256', 'bytes']}
        if key in seen:
            compare(f'artifact {key[0]}:{key[1]}', expected, seen[key])
            return
        if key in sources:
            source = sources[key]
            compare(f'source reference {key[0]}:{key[1]}',
                    {k: source[k] for k in ['sha256', 'bytes']}, expected)
            verify_source(source, locations, revisions)
        else:
            verify_artifact(artifact, locations, remote)
        seen[key] = expected
    for item in lock['artifacts']:
        verify(item)
    verify_pi_copies(pack.schemas, baseline, locations)
    verify(release['baseline'])
    verify(release['contract_inventory'])
    for item in baseline['local_sources']:
        verify(item)
    verify_approval(locations)
    print(f'PASS: {len(pack.schemas)} schemas, 32 tool pairs, {cases} fixtures; local source/release hashes', flush=True)
    observed_mac = local_target(locations)
    amendment_path = BASE / AMENDMENT_NAME
    amendment = load(amendment_path) if amendment_path.exists() else None
    verify_mac_target(baseline['mac'], observed_mac, amendment)
    print('PASS: Mac physical developer_knowledge_v10 (330778 points, 1024 dimensions, BM25 idf); versions', flush=True)
    print('Reading bppc frozen payloads, sparse fingerprints, models and 438/199/30 controls (no model execution)...', flush=True)
    observed_remote = remote_target(locations)
    bppc_amendment_path = BASE / BPPC_AMENDMENT_NAME
    bppc_amendment = load(bppc_amendment_path) if bppc_amendment_path.exists() else None
    verify_bppc_target(baseline['remote'], observed_remote, bppc_amendment)
    for value in [release, load(BASE / 'redirects-m1c.json')]:
        for item in artifact_refs(value):
            verify(item, observed_remote)
    for name, count in [('hard', 438), ('easy', 199), ('sanity', 30)]:
        compare(f'{name} control population', count, observed_remote['controls'][name]['count'])
    print(f'PASS: {len(observed_remote["files"])} bppc file hashes; 330778 IDs/payloads/BM25, 328 sources; original labels and M1c redirect', flush=True)
    approval = BASE / 'approval-2026-10-15.json'
    record = __import__('json').loads(approval.read_text()) if approval.exists() else None
    state = f"contracts approved by {record['approved_by']} on {record['approved_at']}" if record else 'Gary contract approval pending'
    print('PASS: FP P1 mechanical baseline gate; ' + state + '. P7 installation gates remain pending.', flush=True)


if __name__ == '__main__':
    try:
        check()
    except Exception as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(1)
