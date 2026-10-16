"""Exact, evidence-bound amendments for approved Mac and bppc machine facts."""
import copy
import hashlib
import json
import subprocess
import tomllib

from baseline_io import BASE, ROOT, compare, fingerprint, git_fingerprint, load

APPROVAL_REVISION = 'ba264d76b879a8e9672c1f05fd9c2f8f305f1c01'
MERGE_REVISION = '2b35da9'
AMENDMENT_NAME = 'serving-stack-amendment-2026-10-16.json'
BPPC_AMENDMENT_NAME = 'bppc-machine-amendment-2026-10-15.json'


def approval_binding(record):
    payload = {key: value for key, value in record.items() if key != 'approval_binding_sha256'}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def verify_frozen_baseline(record):
    compare('amendment baseline location', {'backend': 'repo', 'path': 'data/baseline/baseline.json'},
            record['baseline']['location'])
    compare('amendment frozen baseline', fingerprint(BASE / 'baseline.json'),
            {key: record['baseline'][key] for key in ['sha256', 'bytes']})


def amended_machine(expected, record):
    compare('amendment approval schema', 'fp/serving-stack-amendment@1', record['schema_version'])
    compare('amendment approval owner', 'Gary', record['approved_by'])
    compare('amendment approval date', '2026-10-16', record['approved_at'])
    compare('amendment approval binding', record['approval_binding_sha256'], approval_binding(record))
    verify_frozen_baseline(record)
    source = record['approval_source']
    compare('amendment approval revision', APPROVAL_REVISION, source['revision'])
    paths = ['data/bench/gate-v11.json', 'data/bench/gate-v11.md', 'uv.lock']
    compare('amendment approval artifact inventory', paths,
            [item['location']['path'] for item in source['artifacts']])
    for artifact in source['artifacts']:
        compare('amendment approval backend', 'repo', artifact['location']['backend'])
        committed = git_fingerprint(artifact['location'], {'roots': {'repo': str(ROOT)}}, source['revision'])
        compare('amendment approval source ' + artifact['location']['path'], committed,
                {key: artifact[key] for key in ['git_blob', 'sha256', 'bytes']})
        if artifact['location']['path'] != 'uv.lock':
            compare('amendment gate binding ' + artifact['location']['path'],
                    {key: committed[key] for key in ['sha256', 'bytes']},
                    fingerprint(ROOT / artifact['location']['path']))
    gate = load(ROOT / paths[0])
    compare('amendment gate verdict', 'PASS', gate['verdict'])
    compare('amendment gate date', record['approved_at'], gate['gate_run']['date'])
    compare('amendment gate collection', 'developer_knowledge_v11', gate['collection'])
    compare('amendment switch approval', True, gate['alias']['merge_approved'])
    compare('amendment implementation commit', MERGE_REVISION, gate['alias']['main_commit'])
    # Read approved dependency versions from Git, never today's mutable lockfile.
    lock_blob = source['artifacts'][-1]['git_blob']
    lock = subprocess.check_output(['git', 'cat-file', 'blob', lock_blob], cwd=ROOT, text=True)
    packages = {item['name']: item['version'] for item in tomllib.loads(lock)['package']}
    compare('amendment package scope', ['torchvision', 'transformers'], sorted(record['changes']))
    machine = copy.deepcopy(expected)
    for name, change in sorted(record['changes'].items()):
        compare('amendment original version ' + name, expected['query_packages'].get(name), change['before'])
        compare('amendment approved version ' + name, packages[name], change['after'])
        machine['query_packages'][name] = change['after']
    return machine


def amended_bppc_machine(expected, record):
    compare('bppc amendment approval schema', 'fp/bppc-machine-amendment@1', record['schema_version'])
    compare('bppc amendment approval owner', 'Gary', record['approved_by'])
    compare('bppc amendment approval date', '2026-10-15', record['approved_at'])
    compare('bppc amendment approval binding', record['approval_binding_sha256'], approval_binding(record))
    compare('bppc amendment reason', 'OS update reboot', record['reason'])
    verify_frozen_baseline(record)
    # The P1g2/P1g3 briefs are the authority; rebinding cannot authorize new values.
    compare('bppc amendment change scope', {
        'kernel': {'before': '7.0.0-28-generic', 'after': '7.0.0-38-generic'},
        'os': {'before': 'Ubuntu 24.04.4 LTS', 'after': 'Ubuntu 24.04.5 LTS'},
    }, record['changes'])
    machine = dict(expected)
    for name, change in sorted(record['changes'].items()):
        compare('bppc amendment original ' + name, expected[name], change['before'])
        machine[name] = change['after']
    return machine
