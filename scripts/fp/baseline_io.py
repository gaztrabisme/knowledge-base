"""Small shared read-only helpers for capture, verification and focused tests."""
import hashlib
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'data/baseline'


def fingerprint(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return {'sha256': digest.hexdigest(), 'bytes': Path(path).stat().st_size}


def load(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def roots(locations):
    values = {'repo': str(ROOT), **locations['roots']}
    for name, variable in [('main-checkout', 'FP_MAIN_CHECKOUT'), ('pi-mind', 'FP_PI_MIND_ROOT'), ('bppc', 'FP_BPPC_ROOT')]:
        if name in values:
            values[name] = os.environ.get(variable, values[name])
    return values


def relative_path(location):
    child = Path(location['path'])
    if child.is_absolute() or '..' in child.parts or not child.parts:
        raise ValueError('artifact path must stay relative to its configured root')
    return child


def resolve(location, locations):
    base = Path(roots(locations)[location['backend']]).expanduser().resolve()
    child = relative_path(location)
    result = (base / child).resolve()
    if not result.is_relative_to(base):
        raise ValueError('artifact symlink escapes configured root')
    return result


def verify_artifact(artifact, locations, remote=None):
    location = artifact['location']
    if location['backend'] == 'bppc':
        if remote is None:
            raise ValueError('remote evidence is required')
        actual = remote['files'].get(location['path'])
    else:
        actual = fingerprint(resolve(location, locations))
    expected = {key: artifact[key] for key in ['sha256', 'bytes']}
    if actual != expected:
        raise ValueError(f'missing/changed artifact: {location["backend"]}:{location["path"]}')


def git_fingerprint(location, locations, commit):
    """Read a committed blob, independently of HEAD, index and working-tree files."""
    path = relative_path(location).as_posix()
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', commit):
        raise ValueError('Git source revision must be a full commit ID')
    root = Path(roots(locations)[location['backend']]).expanduser()
    label = f'{location["backend"]}:{path}'

    def git(*args):
        result = subprocess.run(['git', *args], cwd=root, capture_output=True)
        if result.returncode:
            raise ValueError(f'missing Git commit/blob: {commit}:{label}')
        return result.stdout

    if git('cat-file', '-t', commit).strip() != b'commit':
        raise ValueError(f'missing Git commit: {commit}')
    blob = git('rev-parse', '--verify', f'{commit}:{path}').decode().strip()
    content = git('cat-file', 'blob', blob)
    return {'git_blob': blob, 'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)}


def report_source_drift(artifact, locations, always=False):
    """Mutable source availability/content is diagnostic, never baseline evidence."""
    expected = {key: artifact[key] for key in ['sha256', 'bytes']}
    try:
        unchanged = fingerprint(resolve(artifact['location'], locations)) == expected
    except (OSError, ValueError):
        unchanged = False
    if always or not unchanged:
        location = artifact['location']
        state = 'unchanged' if unchanged else 'changed since baseline'
        print(f'INFO: {location["backend"]}:{location["path"]}: {state}', flush=True)


def verify_source(artifact, locations, revisions):
    """Apply the recorded source policy; instruments and release bytes stay strict."""
    policy = artifact.get('verification', 'strict')
    if policy == 'git':
        location = artifact['location']
        expected = {key: artifact[key] for key in ['git_blob', 'sha256', 'bytes']}
        actual = git_fingerprint(location, locations, revisions[location['backend']])
        compare(f'Git source {location["backend"]}:{location["path"]}', expected, actual)
        report_source_drift(artifact, locations)
    elif policy == 'observation':
        report_source_drift(artifact, locations, always=True)
    elif policy == 'strict':
        verify_artifact(artifact, locations)
    else:
        raise ValueError(f'unknown source verification policy: {policy}')


def api(url, path):
    with urllib.request.urlopen(url.rstrip('/') + path, timeout=15) as response:
        return json.load(response)


def local_target(locations):
    url = os.environ.get('FP_QDRANT_URL', locations['mac_qdrant_url'])
    info = api(url, '/collections/developer_knowledge_v10')['result']
    main = Path(roots(locations)['main-checkout'])
    project_python = str(main / '.venv/bin/python')
    package_code = "import importlib.metadata,json; print(json.dumps({p:importlib.metadata.version(p) for p in ['torch','transformers','torchvision','sentence-transformers','fastembed','qdrant-client']}))"
    return {'aliases': api(url, '/aliases')['result']['aliases'],
            'collection': {'name': 'developer_knowledge_v10', 'points_count': info['points_count'], 'config': info['config']},
            'machine': {'os': 'macOS ' + platform.mac_ver()[0], 'kernel': platform.release(),
                        'architecture': platform.machine(), 'python_checker': platform.python_version(),
                        'python_query': subprocess.check_output([project_python, '--version'], text=True).strip(),
                        'qdrant': {key: api(url, '/')[key] for key in ['version', 'commit']},
                        'query_packages': json.loads(subprocess.check_output([project_python, '-c', package_code], text=True))}}


def remote_target(locations):
    remote_root = roots(locations)['bppc']
    command = 'python3 - ' + shlex.quote(remote_root)
    hosts = [os.environ['FP_BPPC_HOST']] if os.environ.get('FP_BPPC_HOST') else locations['bppc_hosts']
    # LAN first, Tailscale second. Connection failures only; never retry an evidence failure.
    for host in hosts:
        result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=3',
                                 '-o', 'StrictHostKeyChecking=yes', 'bppc@' + host, command],
                                input=(ROOT / 'scripts/fp/remote_probe.py').read_text(),
                                capture_output=True, text=True, timeout=180)
        if result.returncode == 255:
            continue
        if result.returncode:
            raise ValueError(f'bppc probe failed (exit {result.returncode}): {result.stderr[-1800:]}')
        return json.loads(result.stdout)
    raise ValueError('bppc is unreachable; remote verification is mandatory')


def compare(label, expected, actual):
    if expected != actual:
        if isinstance(expected, dict) and isinstance(actual, dict):
            for key in sorted(set(expected) | set(actual)):
                if expected.get(key) != actual.get(key):
                    compare(f'{label}.{key}', expected.get(key), actual.get(key))
        raise ValueError(f'changed baseline: {label}')


def release_models(baseline):
    """Profiles of the saved control; not a claim about original build provenance."""
    result = []
    for name, model in baseline['remote']['models'].items():
        result.append({'model_id': name, 'revision': model['revision'],
            'dimension': baseline['runtime_profile']['dimension'] if name.startswith('jinaai/') else None,
            'precision': 'sparse' if name == 'Qdrant/bm25' else 'float32',
            'query_role': 'retrieval.query' if name.startswith('jinaai/') else 'query-document pair' if name.startswith('cross-encoder/') else 'BM25 query',
            'document_role': 'retrieval.passage' if name.startswith('jinaai/') else 'descriptive-heading + child text' if name.startswith('cross-encoder/') else 'BM25 document',
            'normalization': 'L2' if name.startswith('jinaai/') else 'not applicable',
            'runtime_packages': baseline['remote']['controls']['hard']['identity']['packages']})
    return result
