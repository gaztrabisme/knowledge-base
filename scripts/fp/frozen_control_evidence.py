"""Read bppc's hash-pinned frozen files and extract hashes for EVERY control hit.

Remote program is sent on SSH stdin. It imports only the standard library, opens
files read-only, and loads no KB modules, models, GPU libraries or remote output.
"""
import json
import os
import subprocess

from catalog_io import ROOT, canonical, control_bytes, load


def frozen_control_evidence():
    baseline = load(ROOT/'data/baseline/baseline.json')
    locations = load(ROOT/'data/baseline/locations.json')
    hits = {}
    for name in ('hard','easy','sanity'):
        queries = [json.loads(line) for line in control_bytes(name).splitlines()]
        if len(queries) != baseline['remote']['controls'][name]['count']:
            raise ValueError('control query count differs')
        for query in queries:
            for hit in query['candidates']:
                hits.setdefault(hit['book'],set()).add(hit['parent_id'])
    config = {'root':os.environ.get('FP_BPPC_ROOT',locations['roots']['bppc']),
              'hits':{k:sorted(v) for k,v in hits.items()},
              'files':{f'frozen/{book}.jsonl':baseline['remote']['files'][f'frozen/{book}.jsonl'] for book in hits}}
    program = '''import hashlib,json,sys
from pathlib import Path
config=json.loads(CONFIG_JSON)
root=Path(config['root'])
result={}
for book,wanted in config['hits'].items():
    relative='frozen/'+book+'.jsonl'
    expected=config['files'][relative]
    h=hashlib.sha256(); size=0; parents={}; snippets={}
    with (root/relative).open('rb') as f:
        for line in f:
            h.update(line);size+=len(line)
            row=json.loads(line);p=row['payload'];pid=p['parent_id']
            if pid not in wanted:continue
            sha=hashlib.sha256(p['parent_text'].encode()).hexdigest()
            if pid in parents and parents[pid]!=sha:raise ValueError('conflicting frozen parent '+pid)
            parents[pid]=sha
            snippets.setdefault(pid,set()).add(hashlib.sha256(p['child_text'][:600].encode()).hexdigest())
    if h.hexdigest()!=expected['sha256'] or size!=expected['bytes']:raise ValueError('changed frozen file '+relative)
    if set(parents)!=set(wanted):raise ValueError('missing control evidence '+book)
    result.update({pid:{'parent_sha256':sha,'snippet_sha256':sorted(snippets[pid])} for pid,sha in parents.items()})
print(json.dumps(result))
'''.replace('CONFIG_JSON',repr(canonical(config).decode()))
    hosts=[os.environ['FP_BPPC_HOST']] if os.environ.get('FP_BPPC_HOST') else locations['bppc_hosts']
    for host in hosts:
        response=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=3','-o','StrictHostKeyChecking=yes',
            'bppc@'+host,'python3 -'],input=program,capture_output=True,text=True,timeout=180)
        if response.returncode==255:continue
        if response.returncode:raise ValueError('frozen control evidence failed: '+response.stderr[-800:])
        return json.loads(response.stdout)
    raise ValueError('bppc unreachable; frozen payload evidence required')
