"""First capture of the P1 baseline. Refuses to overwrite an existing freeze.

No remote writes; capture requires already generated schemas and approved-source paths.
This is a builder, never called by check-baseline.sh. Re-freezing is a new decision.
"""
import argparse
import importlib.metadata
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from baseline_io import BASE, ROOT, dump, fingerprint, git_fingerprint, load, local_target, roots, release_models
from validate_contracts import Contracts


def artifact(backend, path, location_roots):
    path = str(path)
    return {'location': {'backend': backend, 'path': path}, **fingerprint(Path(location_roots[backend]) / path)}


def capture_source(backend, path, locations, revisions):
    location_roots = roots(locations)
    location = {'backend': backend, 'path': path}
    # Tree membership does not depend on the blob being present. A missing blob is an error.
    result = subprocess.run(['git', '--literal-pathspecs', 'ls-tree', '-z', revisions[backend], '--', path],
                            cwd=location_roots[backend], capture_output=True)
    if result.returncode:
        raise ValueError(f'missing Git source tree: {backend}:{revisions[backend]}')
    if result.stdout:
        return {'location': location, **git_fingerprint(location, locations, revisions[backend]),
                'verification': 'git'}
    return {**artifact(backend, path, location_roots), 'verification': 'observation'}


def capture(remote_path):
    if (BASE / 'baseline.json').exists():
        raise ValueError('baseline already exists; do not overwrite a frozen record')
    locations = load(BASE / 'locations.json')
    location_roots = roots(locations)
    revisions = {backend: subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                 cwd=location_roots[backend], text=True).strip() for backend in ['repo', 'pi-mind']}

    remote = load(remote_path)
    local = local_target(locations)
    assert {'alias_name': 'developer_knowledge', 'collection_name': 'developer_knowledge_v10'} in local['aliases']
    now = datetime.now(timezone.utc).isoformat()
    refs = []
    for name in ['design-spec.md', 'product-brief.md']:
        refs.append({**artifact('main-checkout', 'data/intake/kbu-2026-10-07/' + name, location_roots),
                     'verification': 'observation'})
    for name in ['CLAUDE.md', 'pyproject.toml', 'knowledge_base/server.py', 'knowledge_base/config.py',
                 'knowledge_base/embedder.py', 'knowledge_base/search.py', 'knowledge_base/index.py',
                 'knowledge_base/chunk.py', 'scripts/eval_retrieval.py', 'scripts/significance.py',
                 'scripts/bench_latency.py', 'scripts/check_catalog.py', 'data/bench/gate-v10.md']:
        refs.append(capture_source('repo', name, locations, revisions))
    for name in ['packages/mind-mcp/src/inputs.ts', 'packages/mind-mcp/src/service.ts',
                 'packages/mind-mcp/src/server.ts', 'packages/contracts/src/common.ts',
                 'packages/contracts/src/memory.ts', 'packages/contracts/package.json']:
        refs.append(capture_source('pi-mind', name, locations, revisions))
    imports = [p for p in (BASE / 'contracts/v1').glob('*.json') if load(p)['$id'].startswith('urn:pi-mind:')]
    for path in imports:
        for prefix in ['packages/contracts/schemas', 'packages/contracts/test/fixtures']:
            refs.append(capture_source('pi-mind', f'{prefix}/{path.name}', locations, revisions))
    decisions = (Path(location_roots['main-checkout']) / 'wiki/decisions.md').read_text()
    block = decisions.split('## Organized mind: product brief and design approved (2026-10-14)', 1)[1].split('\n## ', 1)[0]
    log = (Path(location_roots['main-checkout']) / 'wiki/log.md').read_text().splitlines()
    approval = {'decision_heading': '## Organized mind: product brief and design approved (2026-10-14)',
                'decision_body': block, 'log_lines_241_242': log[240:242],
                'clarification': 'Gary choice 1: pi-mind owns the harness side; KB and archive keep their own repos; one shared interface and installer. Choice 2: Mac runs harness, writer and infrastructure; bppc only the sandboxed LLM engine.',
                'contract_approval': 'pending Gary/coordinator review; whole-design approval is preserved separately'}
    dump(BASE / 'approval-source.json', approval)
    release_parts = load(Path(location_roots['main-checkout']) / 'dist/release/manifest.json')
    assert release_parts['tag'] == 'data-v10'
    assert release_parts['collections']['developer_knowledge_v10']['points'] == 330778
    refs.append(artifact('main-checkout', 'dist/release/manifest.json', location_roots))
    parts = []
    for bundle in release_parts['bundles'].values():
        for part in bundle['parts']:
            item = artifact('main-checkout', 'dist/release/' + part['name'], location_roots)
            assert item['sha256'] == part['sha256'] and item['bytes'] == part['size'], part['name']
            parts.append(item)
    refs.extend(parts)
    remote_ref = lambda path: {'location': {'backend': 'bppc', 'path': path}, **remote['files'][path]}
    dump(BASE / 'redirects-m1c.json', {
        'schema_version': 'mind/label-redirect@1', 'mapping_artifact': remote_ref('m1c/mapping.json'),
        'source_generation': 'developer_knowledge_v10', 'destination_generation': 'kbu_m1_gemma768_cur',
        'interpretation': 'Label correspondence by literal token overlap; not a semantic relevance review or a source/locator replacement. Original labels and control stay unchanged. Unmapped parents remain explicit.',
        **remote['redirect']})
    baseline = {'schema_version': 'mind/baseline@1', 'release_id': 'v10-fp-p1', 'captured_at': now,
                'source_revisions': revisions,
                'approval_state': 'contracts-pending-review', 'remote': remote, 'mac': local,
                'local_sources': refs, 'server': {'version': '0.1.0',
                    'revision': revisions['repo'],
                    'file': next(x for x in refs if x['location']['path'] == 'knowledge_base/server.py')},
                'runtime_profile': {'dense_model': 'jinaai/jina-embeddings-v5-text-small-retrieval', 'dimension': 1024,
                    'query_role': 'retrieval.query', 'document_role': 'retrieval.passage', 'normalization': 'L2',
                    'precision': 'float32', 'sparse_model': 'Qdrant/bm25', 'sparse_modifier': 'idf', 'fusion': 'DBSF',
                    'dense_candidates': 50, 'sparse_candidates': 50, 'fused_candidates': 50, 'top_k': 10,
                    'reranker': 'cross-encoder/ettin-reranker-150m-v1', 'rerank_input': 'descriptive-heading',
                    'score_floor': 4, 'minimum_results': 3, 'child_max_tokens': 250, 'parent_max_tokens': 1900,
                    'query_device': 'cuda (recorded M1 control; no models run by P1)',
                    'historical_index_checkpoint_proof': 'not found; single offline M1 cache pins current control models, while data-v10 part hashes preserve the original index bytes'},
                'validator': {'jsonschema': importlib.metadata.version('jsonschema')},
                'boundaries': ['bppc has no alias: it is the control mirror, not the approved future infrastructure host',
                    'physical Mac developer_knowledge_v10 remains strict; the current developer_knowledge alias target is informational',
                    'source file hashes in frozen manifest predate the M1 PostgreSQL restoration; frozen payload/sparse JSONL is the v10 membership authority',
                    'no new benchmark, model loads, GPU usage or promotion by P1']}
    pi_root = Path(location_roots['pi-mind'])
    pi_revision = revisions['pi-mind']
    # Release contract file pins retain their SHA-256/size shape; baseline local_sources owns Git policy.
    file_pin = lambda item: {key: item[key] for key in ['location', 'sha256', 'bytes']}
    baseline['component_pins'] = [
        {'role': 'knowledge-base', 'repository': 'gaztrabisme/knowledge-base', 'revision': baseline['server']['revision'],
         'dirty': True, 'status': 'included', 'file_pins': [file_pin(x) for x in refs if x['location']['backend'] == 'repo']},
        {'role': 'harness', 'repository': 'pi-mind', 'revision': pi_revision,
         'dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=pi_root, text=True)),
         'status': 'reference-only', 'file_pins': [file_pin(x) for x in refs if x['location']['backend'] == 'pi-mind']},
    ]
    dump(BASE / 'baseline.json', baseline)
    # Lock every schema and fixture, plus registries/provenance and the checking instruments.
    locked_paths = sorted([*list((BASE / 'contracts/v1').glob('*.json')), *list((BASE / 'fixtures/v1').glob('*.json')),
        *[BASE / x for x in ['tools-v1.json', 'pi-inputs-v1.json', 'locations.json', 'approval-source.json', 'redirects-m1c.json', 'disagreements.json', 'CONTRACTS.md']],
        *list((ROOT / 'scripts/fp').glob('*.py')), ROOT / 'scripts/fp/check-baseline.sh', ROOT / 'scripts/fp/requirements.txt',
        ROOT / 'tests/test_fp_baseline.py', ROOT / '.gitignore'])
    dump(BASE / 'contracts-lock.json', {'schema_version': 'mind/contracts-lock@1',
         'artifacts': [artifact('repo', p.relative_to(ROOT), location_roots) for p in locked_paths]})
    release = {'schema_version': 'mind/tested-release@1', 'release_id': 'data-v10-fp-baseline', 'created_at': now,
        'deployment_state': 'baseline-only', 'privacy_scope': 'owner-private',
        'baseline': artifact('repo', 'data/baseline/baseline.json', location_roots),
        'contract_inventory': artifact('repo', 'data/baseline/contracts-lock.json', location_roots),
        'components': baseline['component_pins'],
        'models': release_models(baseline),
        'routing': {'alias': 'developer_knowledge', 'physical_collection': 'developer_knowledge_v10',
                    'embedding_space': 'jina-v5-1024-' + remote['models']['jinaai/jina-embeddings-v5-text-small-retrieval']['revision'],
                    'source_generation': remote['membership']['sha256']},
        'data_artifacts': [remote_ref(path) for path in remote['files'] if path.startswith('gate/v10-') or path in
             ['frozen/manifest.json', 'm1c/mapping.json', 'kb/data/gate-v10/sanity-plan.jsonl',
              'kb/data/gate-v10/sanity.jsonl', 'kb/data/golden/golden_queries_hard.jsonl', 'kb/data/golden/golden_queries.jsonl']],
        'data_parts': parts,
        'installation_matrix': [
             {'machine': 'Mac', 'os': local['machine']['os'], 'python': local['machine']['python_query'],
              'qdrant': local['machine']['qdrant']['version'], 'capability': 'alias/collection identity', 'verdict': 'verified',
              'receipt': artifact('repo', 'data/baseline/baseline.json', location_roots)},
             {'machine': 'bppc', 'os': remote['machine']['os'], 'python': remote['machine']['python_gate'],
              'qdrant': remote['machine']['qdrant']['version'], 'capability': 'v10 matched retrieval control', 'verdict': 'verified',
              'receipt': remote_ref('gate/v10-hard.meta.json')},
             {'machine': 'Mac', 'os': local['machine']['os'], 'python': local['machine']['python_query'],
              'qdrant': local['machine']['qdrant']['version'], 'capability': 'joined gateway and harness matrix', 'verdict': 'untested', 'receipt': None}],
        'capabilities': [
             {'name': 'v10 retrieval control (438/199/30)', 'state': 'verified', 'evidence': [remote_ref('gate/v10-hard.meta.json')],
              'reason': 'Saved M1 fresh control outputs and original labels; P1 verified identities and hashes without running retrieval'},
             {'name': 'catalog/archive/shared memory/gateway', 'state': 'pending', 'evidence': [], 'reason': 'P2-P7 implementation and target installation receipts pending'},
             {'name': 'Gemma promotion/figure ranking/graph', 'state': 'excluded', 'evidence': [], 'reason': 'Separate authorized gates; not part of this frozen v10 release'}],
        'pending_gates': ['Gary contract approval', 'P7 component and data activation receipts', 'Mac end-to-end retrieval/installation checks', 'supported harness subset checks'],
        'rollback': {'routing': 'developer_knowledge_v10 + matching Jina query profile', 'membership_manifest': remote_ref('frozen/manifest.json')},
        'mutable_state_policy': {'journal_in_release': False, 'outbox_in_release': False, 'install_preserves_journal_and_outbox': True}}
    Contracts().validate('tested-release', release)
    dump(BASE / 'tested-release-v10.json', release)
    print(f'Frozen v10: {remote["membership"]["points"]} points, {remote["membership"]["sources"]} sources; contracts await review.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote-observation', type=Path, required=True)
    capture(parser.parse_args().remote_observation)
