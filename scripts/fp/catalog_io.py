"""FP catalog I/O. No model imports and only read operations against services."""
import hashlib
import json
import os
import shlex
import sqlite3
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECORDS = ROOT / 'data/catalog-fp'
MAIN = Path(os.environ.get('FP_MAIN_CHECKOUT', '/Users/GaryT/Documents/Work/tools/knowledge-base'))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(canonical(value) + b'\n')


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def data_dir():
    # The permanent home wins. Staged fallback permits sandbox acceptance before transfer.
    if os.environ.get('FP_DATA_DIR'):
        return Path(os.environ['FP_DATA_DIR']).expanduser()
    permanent = MAIN / 'data/fp'
    return permanent if (permanent / 'catalog.sqlite').exists() else ROOT / 'data/fp'


def connect(path=None):
    path = (Path(path) if path else data_dir() / 'catalog.sqlite').resolve()
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    return db


def qdrant(route, body=None):
    url = os.environ.get('FP_QDRANT_URL', 'http://127.0.0.1:6333')
    req = urllib.request.Request(url.rstrip('/') + '/' + route,
        data=canonical(body) if body is not None else None,
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)['result']


def scroll(collection, payload=True):
    offset = None
    while True:
        body = {'limit': 1000, 'with_payload': payload, 'with_vector': False}
        if offset is not None:
            body['offset'] = offset
        result = qdrant(f'collections/{collection}/points/scroll', body)
        yield from result['points']
        offset = result.get('next_page_offset')
        if offset is None:
            break


def read_remote_file(relative):
    locations = load(ROOT / 'data/baseline/locations.json')
    baseline = load(ROOT / 'data/baseline/baseline.json')
    expected = baseline['remote']['files'][relative]
    root = os.environ.get('FP_BPPC_ROOT', locations['roots']['bppc'])
    if Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('remote path escapes baseline root')
    hosts = [os.environ['FP_BPPC_HOST']] if os.environ.get('FP_BPPC_HOST') else locations['bppc_hosts']
    for host in hosts:
        result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=yes', 'bppc@' + host,
            'cat -- ' + shlex.quote(str(Path(root) / relative))], capture_output=True, timeout=60)
        if result.returncode == 255:
            continue
        if result.returncode:
            raise ValueError(f'read-only SSH failed: {relative}')
        if len(result.stdout) != expected['bytes'] or digest(result.stdout) != expected['sha256']:
            raise ValueError(f'changed frozen file: {relative}')
        return result.stdout
    raise ValueError('bppc unavailable; no unverified control-file fallback')


def control_bytes(name):
    relative = f'gate/v10-{name}.jsonl'
    path = data_dir() / relative
    expected = load(ROOT / 'data/baseline/baseline.json')['remote']['files'][relative]
    if path.exists():
        content = path.read_bytes()
        if len(content) != expected['bytes'] or digest(content) != expected['sha256']:
            raise ValueError(f'changed local control: {relative}')
        return content
    return read_remote_file(relative)
