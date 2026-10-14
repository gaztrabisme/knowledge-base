"""Generate the reviewable v1 contract pack; no models or services are imported.

Rerun: python3 scripts/fp/build_contracts.py --pi-root /path/to/pi-mind
The source comparison record must be re-frozen explicitly after an approved change.
"""
import argparse
import ast
import copy
import json
import hashlib
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'data/baseline'
SCHEMAS = BASE / 'contracts/v1'
FIXTURES = BASE / 'fixtures/v1'
S = {'type': 'string', 'minLength': 1}
TEXT = {'type': 'string'}
N = {'type': 'integer', 'minimum': 0}
REV = {'type': 'integer', 'minimum': 1}
BOOL = {'type': 'boolean'}
HASH = {'type': 'string', 'pattern': '^[a-f0-9]{64}$'}
DATE = {'type': 'string', 'format': 'date-time'}
SCHEMA_IDS = {}


def obj(properties, optional=()):
    return {'type': 'object', 'properties': properties,
            'required': [key for key in properties if key not in optional], 'additionalProperties': False}


def arr(items, **kwargs):
    return {'type': 'array', 'items': items, **kwargs}


def enum(*values):
    return {'enum': list(values)}


def nullable(value):
    return {'anyOf': [value, {'type': 'null'}]}


def ref(name):
    return {'$ref': SCHEMA_IDS.get(name, f'urn:organized-mind:{name}:1')}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def emit(name, schema, sample, invalid=None):
    schema = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
              '$id': f'urn:organized-mind:{name}:1', 'title': name, **schema}
    SCHEMA_IDS[name] = schema['$id']
    write_json(SCHEMAS / f'{name}.json', schema)
    bad = copy.deepcopy(sample)
    if isinstance(bad, dict):
        bad['undeclared_field'] = 'reject unknown fields'
    else:
        bad = None
    write_json(FIXTURES / f'{name}.json', {
        'valid': [{'name': 'synthetic valid shape', 'value': sample}],
        'invalid': [{'name': 'reject invalid shape', 'value': bad}] + (invalid or [])})
    return sample


def main(pi):
    SCHEMAS.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    # These files remain byte-identical to pi-mind; fixtures retain its independent cases.
    imports = ['memory-record', 'memory-write-receipt', 'lesson-payload', 'lesson-record',
               'feedback-record', 'stale-flag-record', 'target-reference', 'evidence-reference',
               'memory-provenance', 'memory-write-error', 'comment-selector', 'stale-flag-payload',
               'feedback-payload', 'memory-receipt-lookup', 'lesson-revision-request',
               'reviewer-or-check', 'memory-audit-event']
    for name in imports:
        for source, target in [('schemas', SCHEMAS), ('test/fixtures', FIXTURES)]:
            shutil.copyfile(pi / f'packages/contracts/{source}/{name}.json', target / f'{name}.json')
        SCHEMA_IDS[name] = json.loads((SCHEMAS / f'{name}.json').read_text())['$id']
    export = 'import {inputSchemas} from ' + json.dumps(str(pi / 'packages/mind-mcp/src/inputs.ts')) + '; console.log(JSON.stringify(inputSchemas));'
    inputs = json.loads(subprocess.check_output(['bun', '-e', export], text=True))
    # Snapshots of the deployed input schemas; new tool contracts are separately labeled below.
    write_json(BASE / 'pi-inputs-v1.json', inputs)
    privacy = enum('owner-private', 'project-private')
    scope = obj({'owner_scope': S, 'project_scope': S, 'privacy_scope': privacy})
    count = {'oneOf': [obj({'value': N, 'reason': {'const': None}}),
                        obj({'value': {'const': None}, 'reason': {'const': 'not found'}})]}
    date_known = {'oneOf': [obj({'value': {'anyOf': [DATE, {'type': 'string', 'format': 'date'}, {'type': 'string', 'pattern': '^\\d{4}(-(?:0[1-9]|1[0-2]))?$'}]}, 'reason': {'const': None}}),
                             obj({'value': {'const': None}, 'reason': {'const': 'not found'}})]}
    graph_predicate = enum('CONTAINS', 'IMPORTS', 'DEFINES', 'EXPLAINS', 'APPLIED_TO', 'USES', 'ASSUMES', 'COMPARES_WITH', 'CONTRADICTS', 'RECOMMENDS_AGAINST', 'PREREQUISITE_OF', 'IMPLEMENTS')
    source_target = {'allOf': [ref('target-reference'), {'properties': {'target_type': {'const': 'source'}}}]}
    alias = obj({'namespace': S, 'value': S})
    source_ref = obj({'source_id': S, 'source_revision': S, 'source_hash': HASH, 'privacy_scope': privacy})
    source_sample = {'source_id': 'synthetic-book', 'source_revision': 'edition-1',
                     'source_hash': 'a' * 64, 'privacy_scope': 'owner-private'}
    source = emit('source-identity', obj({
        'schema_version': {'const': 'mind/source@1'}, **source_ref['properties'],
        'kind': enum('book', 'course', 'lesson', 'paper', 'repository', 'file', 'symbol'),
        'aliases': arr(alias), 'canonical_url': nullable({'type': 'string', 'format': 'uri', 'pattern': '^https?://'}),
        'title': S, 'creators': arr(S), 'publication_date': date_known, 'revision_date': date_known, 'acquired_at': DATE,
        'selected_scope': S, 'derivation': enum('original', 'translation', 'derived')}), {
        'schema_version': 'mind/source@1', **source_sample, 'kind': 'book', 'aliases': [],
        'canonical_url': None, 'title': 'Synthetic fixture', 'creators': [],
        'publication_date': {'value': None, 'reason': 'not found'}, 'revision_date': {'value': None, 'reason': 'not found'}, 'acquired_at': '2026-10-14T00:00:00Z',
        'selected_scope': 'one chapter', 'derivation': 'original'})
    locators = [
        obj({'kind': {'const': 'markdown-lines'}, 'path': S, 'start_line': REV, 'end_line': REV}),
        obj({'kind': {'const': 'pdf-page'}, 'page': REV, 'page_label': nullable(S),
             'width': {'type': 'number', 'exclusiveMinimum': 0}, 'height': {'type': 'number', 'exclusiveMinimum': 0},
             'rotation': enum(0, 90, 180, 270), 'coordinate_system': {'const': 'top-left-points'},
             'rectangle': nullable(arr({'type': 'number'}, minItems=4, maxItems=4))}),
        obj({'kind': {'const': 'epub-resource'}, 'resource': S, 'reading_order': N, 'start_offset': N, 'end_offset': N}),
        obj({'kind': {'const': 'caption-cue'}, 'lesson_id': S, 'cue_id': S,
             'start_seconds': {'type': 'number', 'minimum': 0}, 'end_seconds': {'type': 'number', 'minimum': 0}}),
        obj({'kind': {'const': 'code-lines'}, 'commit': {'type': 'string', 'pattern': '^(?:[a-f0-9]{40}|[a-f0-9]{64})$'},
             'path': S, 'start_line': REV, 'end_line': REV}),
        obj({'kind': {'const': 'legacy-chunk'}, 'chunk_id': S, 'parent_id': S,
             'page_mapping': {'const': 'not found'}}),
    ]
    locator = {'kind': 'markdown-lines', 'path': 'synthetic.md', 'start_line': 1, 'end_line': 3}
    emit('locator', {'oneOf': locators}, locator, [
        {'name': 'reversed lines', 'value': {**locator, 'end_line': 0}},
        {'name': 'semantic reversed range', 'value': {**locator, 'start_line': 5}}])
    error = obj({'code': enum('validation', 'permission', 'revision_conflict', 'request_key_conflict',
                               'backend_unavailable', 'not_found', 'version_mismatch', 'budget_limit', 'internal'),
                 'message': S, 'retryable': BOOL, 'retry_after_ms': nullable(N)})
    source_mapping = obj({**source_ref['properties'], 'producing_revision': S,
                          'returned_text_hash': HASH, 'locator': ref('locator')})
    metadata = emit('read-metadata', obj({
        'schema_version': {'const': 'mind-read/v1'}, 'read_id': S,
        'backend_availability': enum('ready', 'partial', 'unavailable', 'disabled', 'experimental'),
        'source_snapshot': S, 'index_snapshot': nullable(S), 'graph_snapshot': nullable(S),
        'privacy_scope': privacy, 'sources': arr(source_mapping),
        'legacy_character_truncation': BOOL, 'budget_truncation': BOOL,
        'omitted_count': N, 'cursor': nullable(S), 'errors': arr(error),
        'budget': nullable(obj({'question_budget_id': S, 'tokens_used': N, 'tokens_remaining': N,
                              'counter': S, 'serialization_revision': S}))}), {
        'schema_version': 'mind-read/v1', 'read_id': 'synthetic-read', 'backend_availability': 'ready',
        'source_snapshot': 'v10', 'index_snapshot': 'developer_knowledge_v10', 'graph_snapshot': None,
        'privacy_scope': 'owner-private', 'sources': [{**source_sample, 'producing_revision': 'edition-1',
        'returned_text_hash': hashlib.sha256(b'synthetic fixture').hexdigest(), 'locator': locator}], 'legacy_character_truncation': False,
        'budget_truncation': False, 'omitted_count': 0, 'cursor': None, 'errors': [], 'budget': None})
    evidence = emit('evidence-read', obj({
        'schema_version': {'const': 'mind/evidence-read@1'}, 'evidence_id': S,
        **source_ref['properties'], 'selected_snapshot': S, 'producing_revision': S,
        'locator': ref('locator'), 'content': TEXT, 'content_sha256': HASH,
        'derivation': enum('original', 'translation', 'derived'),
        'verification': enum('exact', 'fuzzy', 'failed', 'unchecked'),
        'annotations': arr(ref('target-reference')), 'metadata': ref('read-metadata')}), {
        'schema_version': 'mind/evidence-read@1', 'evidence_id': 'synthetic-span', **source_sample,
        'selected_snapshot': 'v10', 'producing_revision': 'edition-1', 'locator': locator,
        'content': 'synthetic fixture', 'content_sha256': hashlib.sha256(b'synthetic fixture').hexdigest(), 'derivation': 'original',
        'verification': 'unchecked', 'annotations': [], 'metadata': metadata})
    stage_schema = obj({'state': enum('missing', 'locked', 'failed', 'skipped', 'truncated', 'pending',
                                     'valid-empty', 'completed'), 'expected': count, 'attempted': count,
                        'completed': count, 'profile': nullable(S), 'errors': arr(S)})
    completed_stage = {'state': 'completed', 'expected': {'value': 1, 'reason': None},
                       'attempted': {'value': 1, 'reason': None}, 'completed': {'value': 1, 'reason': None},
                       'profile': 'synthetic-profile', 'errors': []}
    catalog = emit('catalog-entry', obj({
        'schema_version': {'const': 'mind/catalog-entry@1'}, 'source': ref('source-identity'),
        'snapshot': S, 'ordered_membership': arr(S, uniqueItems=True), 'inventory_complete': BOOL,
        'archive': stage_schema, 'parse': stage_schema, 'index': stage_schema, 'extraction': stage_schema,
        'omitted_modalities': arr(enum('text', 'image', 'audio', 'video', 'code'), uniqueItems=True),
        'truncation': BOOL, 'quote_checks': enum('passed', 'failed', 'pending', 'not found'), 'gaps': arr(S)}), {
        'schema_version': 'mind/catalog-entry@1', 'source': source, 'snapshot': 'v10',
        'ordered_membership': ['synthetic-unit'], 'inventory_complete': True,
        **{name: completed_stage for name in ['archive', 'parse', 'index', 'extraction']},
        'omitted_modalities': [], 'truncation': False, 'quote_checks': 'pending', 'gaps': []})
    source_evidence = emit('source-evidence-reference', obj({'type': {'const': 'source_span'}, 'id': S,
        **source_ref['properties'], 'locator': ref('locator'),
        'verification': enum('exact', 'fuzzy', 'failed', 'unchecked')}), {
        'type': 'source_span', 'id': 'synthetic-span', **source_sample, 'locator': locator, 'verification': 'unchecked'})
    emit('contribution-evidence-reference', {'anyOf': [ref('evidence-reference'), ref('source-evidence-reference')]}, source_evidence)
    # New contribution kinds use the same envelope field names as pi-mind, but have new versions.
    pi_record = json.loads((SCHEMAS / 'lesson-record.json').read_text())
    env_fields = copy.deepcopy(pi_record['properties'])
    for key in ['kind', 'payload', 'payload_schema']:
        del env_fields[key]
    env_fields['schema_version'] = {'const': 'mind/annotation-record@1'}
    env_fields['evidence'] = arr(ref('contribution-evidence-reference'))
    env_fields['authority'] = {'const': 'annotation'}
    selector = ref('comment-selector')
    patch = obj({'target': source_target, 'target_hash': HASH, 'before': TEXT, 'after': TEXT,
                 'rationale': S, 'applied': {'const': False}})
    payloads = {
        'stale_flag': obj({'target': ref('target-reference'), 'reason': S, 'detected_at': DATE,
                           'observed_version': S, 'resolution': nullable(S), 'resolved_at': nullable(DATE)}),
        'comment': obj({'target': source_target, 'selector': selector,
                        'relation': enum('question', 'disagreement', 'example', 'note'), 'body': S,
                        'attachment_state': enum('attached', 'detached', 'proposed-reattachment')}),
        'tag': obj({'subject': ref('target-reference'), 'label': S, 'rationale': S}),
        'link': obj({'subject': ref('target-reference'), 'predicate': S, 'object': ref('target-reference'),
                     'rationale': S, 'applicability': S}),
        'source_change': patch,
        'review': obj({'target': ref('target-reference'), 'disposition': enum('verify', 'contest', 'retire',
                       'reject', 'close-stale', 'approve-patch'), 'check': ref('reviewer-or-check'), 'scope': S}),
    }
    selector_sample = json.loads((FIXTURES / 'comment-selector.json').read_text())['valid'][0]['value']
    selector_sample.update(source_id='synthetic-book', source_revision='edition-1')
    target = {'target_type': 'source', 'target_id': 'synthetic-book', 'target_revision': 'edition-1'}
    annotation = json.loads((FIXTURES / 'lesson-record.json').read_text())['valid'][0]['value']
    annotation['authority'] = 'annotation'
    annotation['evidence'] = [source_evidence]
    annotation.update(schema_version='mind/annotation-record@1', kind='comment', payload_schema='mind/comment@1',
                      payload={'target': target, 'selector': selector_sample, 'relation': 'question',
                               'body': 'Synthetic question', 'attachment_state': 'attached'})
    emit('annotation-record', {'oneOf': [obj({**env_fields, 'kind': {'const': kind},
         'payload_schema': {'const': 'mind/stale-flag@2' if kind == 'stale_flag' else f'mind/{kind}@1'}, 'payload': payload}) for kind, payload in payloads.items()]}, annotation)
    emit('shared-memory-record', {'anyOf': [ref('memory-record'), ref('annotation-record')]}, annotation)
    certificate = obj({'snapshot': S, 'scope': S, 'predicate': S, 'profile': S,
                       'required_units': arr(S, minItems=1, uniqueItems=True), 'processing': stage_schema,
                       'omissions': arr(S), 'review_state': enum('pending', 'checked')})
    cert = {'snapshot': 'v10', 'scope': 'one chapter', 'predicate': 'EXPLAINS', 'profile': 'synthetic-profile',
            'required_units': ['synthetic-unit'], 'processing': completed_stage, 'omissions': [], 'review_state': 'pending'}
    coverage = obj({'conclusion': enum('supported', 'unknown', 'no-indexed-evidence-in-scope', 'confirmed-library-gap'),
                    'certificate': certificate, 'evidence': arr(ref('evidence-read')), 'ambiguities': arr(S)})
    coverage_sample = {'conclusion': 'supported', 'certificate': cert, 'evidence': [evidence], 'ambiguities': []}
    assertion = obj({'id': S, 'revision': S, 'subject': S, 'predicate': graph_predicate, 'object': S, 'conditions': TEXT,
                     'negated': BOOL, 'profile': S, 'verification': enum('exact', 'fuzzy', 'failed', 'unchecked'),
                     'evidence': arr(ref('evidence-read'), minItems=1), 'applicability': S})
    edge = {'id': 'synthetic-edge', 'revision': '1', 'subject': 'method', 'predicate': 'EXPLAINS', 'object': 'concept',
            'conditions': 'synthetic scope', 'negated': False, 'profile': 'synthetic-profile', 'verification': 'unchecked',
            'evidence': [evidence], 'applicability': 'one chapter'}
    job = obj({'job_id': S, 'archive': stage_schema, 'kb': stage_schema, 'access_gaps': arr(S)})
    job_sample = {'job_id': 'synthetic-job', 'archive': completed_stage, 'kb': completed_stage, 'access_gaps': []}
    context = obj({**scope['properties'], 'question_budget_id': S}, optional=['question_budget_id'])
    common_write = {key: copy.deepcopy(value) for key, value in inputs['memory_create_lesson']['properties'].items()
                    if key not in ['payload', 'id', 'expected_revision', 'retract']}
    common_write['evidence'] = {'type': 'array', 'items': ref('contribution-evidence-reference')}
    required_write = set(inputs['memory_create_lesson']['required']) - {'payload'}
    write_sample = {'request_key': 'synthetic-request', 'owner_scope': 'owner-1', 'project_scope': 'project-1',
                    'assertion_type': 'observation'}
    schema_set = {}
    samples = {}
    # Derive legacy arguments from syntax, so no models are imported and every signature stays intact.
    legacy = ['search', 'search_book', 'read_chunk', 'get_chapter', 'list_books', 'grep_books',
              'search_philosophy', 'list_philosophy']
    tree = ast.parse((ROOT / 'knowledge_base/server.py').read_text())
    def annotation_schema(node):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return {'anyOf': [annotation_schema(node.left), annotation_schema(node.right)]}
        if isinstance(node, ast.Subscript):
            return arr(annotation_schema(node.slice))
        if isinstance(node, ast.Constant) and node.value is None:
            return {'type': 'null'}
        return {'type': {'str': 'string', 'int': 'integer', 'bool': 'boolean'}[node.id]}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in legacy:
            fields = {a.arg: annotation_schema(a.annotation) for a in node.args.args}
            optional = [a.arg for a in node.args.args[len(node.args.args) - len(node.args.defaults):]]
            for key, default in zip(optional, node.args.defaults):
                fields[key]['default'] = ast.literal_eval(default)
            schema_set[node.name] = obj(fields, optional)
            samples[node.name] = {key: ('synthetic-book' if key == 'book' else 'synthetic')
                                  for key in fields if key not in optional}
    def add(name, fields, sample, optional=()):
        schema_set[name] = obj(fields, optional)
        samples[name] = sample
    add('legacy_read', {'operation': enum(*legacy), 'arguments': {'oneOf': [
        {'allOf': [schema_set[name]]} for name in legacy]}, 'question_budget_id': S, 'cursor': nullable(S)},
        {'operation': 'get_chapter', 'arguments': samples['get_chapter'], 'question_budget_id': 'synthetic-budget'}, ['cursor'])
    # Conditional schemas bind legacy operation to its own arguments; overlapping signatures are valid.
    schema_set['legacy_read']['properties']['arguments'] = {'type': 'object'}
    schema_set['legacy_read']['allOf'] = [
        {'if': {'properties': {'operation': {'const': name}}},
         'then': {'properties': {'arguments': schema_set[name]}}} for name in legacy]
    add('read_metadata', {'read_id': S}, {'read_id': 'synthetic-read'})
    add('mind_status', {'component': enum('all', 'kb', 'memory', 'archive', 'graph')}, {}, ['component'])
    add('source_list', {'kind': enum('book', 'course', 'lesson', 'paper', 'repository', 'file', 'symbol'),
                       'scope': S, 'snapshot': S, 'filters': obj({'source_id': S, 'stage': enum('archive', 'parse', 'index', 'extraction')}, ['source_id', 'stage']),
                       'cursor': nullable(S)}, {'scope': 'one chapter', 'snapshot': 'v10'}, ['kind', 'filters', 'cursor'])
    add('source_read', {'source_id': S, 'unit_id': S, 'revision': S, 'locator': ref('locator'), 'cursor': nullable(S),
                       'budget': obj({'question_budget_id': S, 'max_tokens': REV})},
        {'source_id': 'synthetic-book', 'revision': 'edition-1'}, ['unit_id', 'locator', 'cursor', 'budget'])
    add('figure_read', {'figure_occurrence_id': S, 'source_revision': S},
        {'figure_occurrence_id': 'synthetic-figure', 'source_revision': 'edition-1'})
    add('figure_search', {'query': S, 'scope': S, 'embedding_space': S, 'top_k': REV},
        {'query': 'synthetic', 'scope': 'one chapter', 'embedding_space': 'experimental-space', 'top_k': 5})
    add('coverage', {'topic': S, 'requirement': S, 'predicate': S, 'scope': S, 'as_of': DATE, 'snapshot': S},
        {'topic': 'synthetic', 'requirement': 'introduction', 'scope': 'one chapter', 'snapshot': 'v10'}, ['predicate', 'as_of'])
    add('coverage_gaps', {'requirement_set_id': S, 'scope': S, 'snapshot': S},
        {'requirement_set_id': 'synthetic-requirements', 'scope': 'one chapter', 'snapshot': 'v10'})
    add('graph_subgraph', {'entity_id': S, 'predicates': arr(graph_predicate, minItems=1), 'direction': enum('in', 'out', 'both'), 'cursor': nullable(S)},
        {'entity_id': 'method', 'predicates': ['EXPLAINS'], 'direction': 'out'}, ['cursor'])
    add('graph_evidence', {'entity_id': S, 'assertion_id': S, 'revision': S, 'cursor': nullable(S)},
        {'assertion_id': 'synthetic-edge', 'revision': '1'}, ['entity_id', 'assertion_id', 'cursor'])
    schema_set['graph_evidence']['anyOf'] = [{'required': ['entity_id']}, {'required': ['assertion_id']}]
    add('graph_who_tried', {'method_ids': arr(S, minItems=1), 'problem_ids': arr(S, minItems=1),
        'predicate': graph_predicate, 'direction': enum('in', 'out', 'both'), 'scope': S},
        {'method_ids': ['method'], 'problem_ids': ['problem'], 'predicate': 'APPLIED_TO', 'direction': 'out', 'scope': 'one chapter'})
    for name in ['memory_create_lesson', 'memory_flag_stale', 'memory_feedback', 'memory_read', 'memory_search']:
        schema_set[name] = copy.deepcopy(inputs[name])
    samples['memory_create_lesson'] = {**write_sample, 'payload': json.loads((FIXTURES / 'lesson-payload.json').read_text())['valid'][0]['value']}
    samples['memory_flag_stale'] = {**write_sample, 'target': target, 'reason': 'synthetic recheck'}
    samples['memory_feedback'] = {**write_sample, 'target': target, 'outcome': 'neutral', 'explanation': 'synthetic feedback'}
    samples['memory_read'] = {'id': 'synthetic-lesson'}
    samples['memory_search'] = {'query': 'synthetic'}
    schema_set['memory_search']['properties'].update(history=BOOL, cursor=nullable(S))
    schema_set['memory_search']['not'] = {'required': ['offset', 'cursor']}
    schema_set['memory_read']['anyOf'] = [{'required': ['id']}, {'required': ['request_key']}]
    for name, extra, sample in [
        ('memory_comment', {'target': source_target, 'selector': selector, 'relation': enum('question', 'disagreement', 'example', 'note'), 'body': S},
         {'target': target, 'selector': selector_sample, 'relation': 'question', 'body': 'synthetic question'}),
        ('memory_tag_link', {'subject': ref('target-reference'), 'tag': S, 'predicate': S, 'object': ref('target-reference'), 'rationale': S, 'applicability': S},
         {'subject': target, 'tag': 'synthetic-tag', 'rationale': 'synthetic rationale'}),
        ('memory_propose_source_change', {'target': source_target, 'target_hash': HASH, 'before': TEXT, 'after': TEXT, 'rationale': S},
         {'target': target, 'target_hash': 'a' * 64, 'before': 'before', 'after': 'after', 'rationale': 'synthetic rationale'}),
        ('review_decide', {'target': ref('target-reference'), 'disposition': enum('verify', 'contest', 'retire', 'reject', 'close-stale', 'approve-patch'),
                           'check': ref('reviewer-or-check'), 'expected_revision': REV},
         {'target': {'target_type': 'memory_record', 'target_id': 'synthetic-lesson', 'target_revision': 1},
          'disposition': 'verify', 'check': {'writer': 'owner', 'writer_assurance': 'authenticated'}, 'expected_revision': 1}),
    ]:
        optional = list(set(common_write) - required_write)
        if name == 'memory_tag_link':
            optional += ['tag', 'predicate', 'object', 'applicability']
        add(name, {**common_write, **extra}, {**write_sample, **sample}, optional)
    schema_set['memory_tag_link']['oneOf'] = [
        {'required': ['tag'], 'not': {'anyOf': [{'required': ['predicate']}, {'required': ['object']}]}},
        {'required': ['predicate', 'object', 'applicability'], 'not': {'required': ['tag']}}]
    add('review_queue', {'scope': S, 'reason': S, 'status': enum('pending', 'decided'), 'cursor': nullable(S)},
        {'scope': 'one chapter'}, ['reason', 'status', 'cursor'])
    add('archive_prepare', {'adapter': enum('domestika', 'coursera', 'book', 'paper', 'repository'),
                           'selected_locator': S, 'revision': S, 'scope': S, 'requirements': arr(S, minItems=1)},
        {'adapter': 'book', 'selected_locator': 'synthetic-local-file', 'revision': 'edition-1', 'scope': 'one chapter', 'requirements': ['text']})
    add('archive_job_status', {'job_id': S}, {'job_id': 'synthetic-job'})
    # Legacy output types are deliberately preserved; the transport carries metadata separately.
    legacy_types = {'search': arr({'type': 'object'}), 'search_book': arr({'type': 'object'}),
                    'read_chunk': {'type': 'object'}, 'get_chapter': TEXT,
                    'list_books': {'anyOf': [arr({'type': 'object'}), {'type': 'object'}]},
                    'grep_books': arr({'type': 'object'}), 'search_philosophy': arr({'type': 'object'}),
                    'list_philosophy': {'type': 'object'}}
    legacy_samples = {name: ([] if name in ['search', 'search_book', 'grep_books', 'search_philosophy'] else {}) for name in legacy}
    legacy_samples['get_chapter'] = '# Synthetic chapter\n'
    hit = {'score': 4.5, 'book': 'synthetic-book', 'book_title': 'Synthetic fixture', 'heading_path': 'Chapter 1', 'text': 'synthetic fixture', 'chunk_id': 'synthetic-child'}
    legacy_samples.update(search=[hit], search_book=[hit], read_chunk={'chunk_id': 'synthetic-child', 'content': 'synthetic fixture', 'previous': None, 'next': None}, grep_books=[{'book': 'synthetic-book', 'line_number': 1, 'context': 'synthetic fixture'}], list_books=[{'slug': 'synthetic-book', 'title': 'Synthetic fixture', 'domain': 'software-engineering', 'chapter_count': 1}], search_philosophy=[{'work': 'synthetic-work', 'section': '1', 'text': 'synthetic fixture', 'parallels': {}}], list_philosophy={'works': [{'work': 'synthetic-work', 'languages': ['en']}]})
    fixture_record = json.loads((FIXTURES / 'lesson-record.json').read_text())['valid'][0]['value']
    receipt = json.loads((FIXTURES / 'memory-write-receipt.json').read_text())['valid'][0]['value']
    figure = obj({'figure_occurrence_id': S, **source_ref['properties'], 'locator': ref('locator'),
                  'asset_path': S, 'asset_sha256': HASH, 'caption': TEXT, 'context': TEXT,
                  'requested_time_seconds': nullable({'type': 'number', 'minimum': 0}),
                  'actual_time_seconds': {'oneOf': [obj({'value': {'type': 'number', 'minimum': 0}, 'reason': {'const': None}}), obj({'value': {'const': None}, 'reason': {'const': 'not found'}})]}})
    figure_sample = {'figure_occurrence_id': 'synthetic-figure', **source_sample, 'locator': locator,
                     'asset_path': 'figures/synthetic.png', 'asset_sha256': 'd' * 64,
                     'caption': 'Synthetic caption', 'context': 'Synthetic context', 'requested_time_seconds': None,
                     'actual_time_seconds': {'value': None, 'reason': 'not found'}}
    records = arr(ref('shared-memory-record'))
    outputs = {
        'read_metadata': (ref('read-metadata'), metadata),
        'mind_status': (obj({'release_id': S, 'components': arr(obj({'component': S, 'state': enum('ready', 'unavailable', 'pending', 'disabled')})),
                            'pending_jobs': N, 'synchronized_revision': nullable(REV)}),
                        {'release_id': 'v10-baseline', 'components': [{'component': 'kb', 'state': 'ready'}], 'pending_jobs': 0, 'synchronized_revision': None}),
        'source_list': (arr(ref('catalog-entry')), [catalog]), 'source_read': (arr(ref('evidence-read')), [evidence]),
        'figure_read': (figure, figure_sample), 'figure_search': (arr(figure), [figure_sample]),
        'coverage': (coverage, coverage_sample),
        'coverage_gaps': (arr(obj({'requirement_id': S, 'state': enum('not-acquired', 'not-indexed', 'extraction-incomplete',
                      'no-extracted-support', 'insufficient-support'), 'certificate': certificate, 'nearby_evidence': arr(ref('evidence-read')),
                      'missing_units': arr(S), 'latest_source_date': date_known, 'next_action': S})),
                      [{'requirement_id': 'synthetic-requirement', 'state': 'extraction-incomplete', 'certificate': cert,
                        'nearby_evidence': [], 'missing_units': ['synthetic-unit'], 'latest_source_date': {'value': None, 'reason': 'not found'}, 'next_action': 'Recheck'}]),
        'graph_subgraph': (arr(assertion), [edge]), 'graph_evidence': (arr(ref('evidence-read')), [evidence]),
        'graph_who_tried': (obj({'relationships': arr(assertion), 'certificate': certificate, 'absence_state': enum('supported', 'unknown', 'no-indexed-evidence-in-scope')}),
                           {'relationships': [edge], 'certificate': cert, 'absence_state': 'supported'}),
        'memory_search': (records, [fixture_record]),
        'memory_read': (obj({'records': records, 'receipt': nullable(ref('memory-write-receipt'))}), {'records': [fixture_record], 'receipt': None}),
        'review_queue': (records, [annotation]), 'archive_prepare': (job, job_sample), 'archive_job_status': (job, job_sample),
    }
    tool_index = []
    for name, arguments in schema_set.items():
        request = {'schema_version': 'mind-tool-request/v1', 'operation': name, 'arguments': samples[name],
                   'context': {'owner_scope': 'owner-1', 'project_scope': 'project-1', 'privacy_scope': 'owner-private'}}
        emit('request.' + name, obj({'schema_version': {'const': 'mind-tool-request/v1'},
             'operation': {'const': name}, 'arguments': arguments, 'context': context}), request,
             [{'name': 'wrong operation', 'value': {**request, 'operation': 'nonexistent_tool'}},
              {'name': 'unknown argument', 'value': {**request, 'arguments': {**samples[name], 'unknown': True}}}])
        if name in legacy:
            response_schema = obj({'legacy_output': legacy_types[name], '_meta': obj({'mind': ref('read-metadata')})})
            response_metadata = copy.deepcopy(metadata)
            if isinstance(legacy_samples[name], str):
                response_metadata['sources'][0]['returned_text_hash'] = hashlib.sha256(legacy_samples[name].encode()).hexdigest()
            response = {'legacy_output': legacy_samples[name], '_meta': {'mind': response_metadata}}
        elif name == 'legacy_read':
            response_schema = {'oneOf': [obj({'operation': {'const': operation}, 'read_id': S,
                               'legacy_output': legacy_types[operation], 'metadata': ref('read-metadata'),
                               'annotations': records}) for operation in legacy]}
            response_metadata = copy.deepcopy(metadata)
            response_metadata['sources'][0]['returned_text_hash'] = hashlib.sha256(legacy_samples['get_chapter'].encode()).hexdigest()
            response = {'operation': 'get_chapter', 'read_id': 'synthetic-read',
                        'legacy_output': legacy_samples['get_chapter'], 'metadata': response_metadata, 'annotations': []}
        elif name.startswith('memory_') and name not in ['memory_read', 'memory_search'] or name == 'review_decide':
            response_schema = obj({'receipt': ref('memory-write-receipt'), 'metadata': ref('read-metadata')})
            response = {'receipt': receipt, 'metadata': metadata}
        else:
            data_schema, data = outputs[name]
            response_schema = obj({'schema_version': {'const': 'mind-tool-response/v1'},
                                   'data': nullable(data_schema), 'metadata': ref('read-metadata')})
            response = {'schema_version': 'mind-tool-response/v1', 'data': data, 'metadata': metadata}
        emit('response.' + name, response_schema, response)
        tool_index.append({'name': name, 'request': f'request.{name}.json', 'response': f'response.{name}.json',
                           'state': 'legacy-compatible' if name in legacy else 'proposed',
                           'permission': 'owner-review' if name == 'review_decide' else 'authorized-archive-job' if name == 'archive_prepare' else
                           'annotation-write' if name.startswith('memory_') and name not in ['memory_read', 'memory_search'] else 'read'})
    write_json(BASE / 'tools-v1.json', {'schema_version': 'mind/tool-registry@1', 'tools': tool_index})
    # P7 fills actual private release parts and receipts; this v10 baseline claims only observed retrieval evidence.
    artifact = obj({'location': obj({'backend': enum('repo', 'main-checkout', 'pi-mind', 'bppc'), 'path': S}), 'sha256': HASH, 'bytes': N})
    emit('tested-release', obj({
        'schema_version': {'const': 'mind/tested-release@1'}, 'release_id': S, 'created_at': DATE,
        'deployment_state': enum('baseline-only', 'tested', 'released'), 'privacy_scope': privacy,
        'baseline': artifact, 'contract_inventory': artifact,
        'components': arr(obj({'role': enum('knowledge-base', 'harness', 'archive', 'graph'), 'repository': S,
                             'revision': {'type': 'string', 'pattern': '^[a-f0-9]{40,64}$'}, 'dirty': BOOL,
                             'status': enum('included', 'reference-only', 'excluded'), 'file_pins': arr(artifact)}), minItems=1),
        'models': arr(obj({'model_id': S, 'revision': S, 'dimension': nullable(REV), 'precision': S, 'query_role': S,
                          'document_role': S, 'normalization': S, 'runtime_packages': obj({'torch': S, 'transformers': S,
                          'sentence-transformers': S, 'fastembed': S, 'qdrant-client': S})}), minItems=1),
        'routing': obj({'alias': S, 'physical_collection': S, 'embedding_space': S, 'source_generation': S}),
        'data_artifacts': arr(artifact, minItems=1), 'data_parts': arr(artifact),
        'installation_matrix': arr(obj({'machine': S, 'os': S, 'python': S, 'qdrant': S,
                    'capability': S, 'verdict': enum('verified', 'untested', 'unavailable'), 'receipt': nullable(artifact)}), minItems=1),
        'capabilities': arr(obj({'name': S, 'state': enum('verified', 'pending', 'excluded'), 'evidence': arr(artifact), 'reason': S}), minItems=1),
        'pending_gates': arr(S, uniqueItems=True), 'rollback': obj({'routing': S, 'membership_manifest': artifact}),
        'mutable_state_policy': obj({'journal_in_release': {'const': False}, 'outbox_in_release': {'const': False},
                                    'install_preserves_journal_and_outbox': {'const': True}})}), {
        'schema_version': 'mind/tested-release@1', 'release_id': 'synthetic-release', 'created_at': '2026-10-14T00:00:00Z',
        'deployment_state': 'baseline-only', 'privacy_scope': 'owner-private',
        'baseline': {'location': {'backend': 'repo', 'path': 'data/baseline/baseline.json'}, 'sha256': 'a' * 64, 'bytes': 1},
        'contract_inventory': {'location': {'backend': 'repo', 'path': 'data/baseline/contracts-lock.json'}, 'sha256': 'a' * 64, 'bytes': 1},
        'components': [{'role': 'knowledge-base', 'repository': 'knowledge-base', 'revision': 'a' * 40, 'dirty': False, 'status': 'included', 'file_pins': []}],
        'models': [{'model_id': 'synthetic-model', 'revision': 'a' * 40, 'dimension': 1024, 'precision': 'float32',
                    'query_role': 'retrieval.query', 'document_role': 'retrieval.passage', 'normalization': 'L2',
                    'runtime_packages': {k: 'synthetic' for k in ['torch', 'transformers', 'sentence-transformers', 'fastembed', 'qdrant-client']}}],
        'routing': {'alias': 'developer_knowledge', 'physical_collection': 'developer_knowledge_v10', 'embedding_space': 'synthetic-space', 'source_generation': 'v10'},
        'data_artifacts': [{'location': {'backend': 'bppc', 'path': 'frozen/manifest.json'}, 'sha256': 'a' * 64, 'bytes': 1}],
        'data_parts': [], 'installation_matrix': [{'machine': 'Mac', 'os': 'synthetic', 'python': 'synthetic', 'qdrant': 'synthetic',
                    'capability': 'retrieval', 'verdict': 'untested', 'receipt': None}],
        'capabilities': [{'name': 'retrieval', 'state': 'pending', 'evidence': [], 'reason': 'synthetic'}], 'pending_gates': ['P7'],
        'rollback': {'routing': 'v10', 'membership_manifest': {'location': {'backend': 'bppc', 'path': 'frozen/manifest.json'}, 'sha256': 'a' * 64, 'bytes': 1}},
        'mutable_state_policy': {'journal_in_release': False, 'outbox_in_release': False, 'install_preserves_journal_and_outbox': True}})
    # Additional branches and failure cases are explicit, so union schemas are exercised.
    def add_case(name, verdict, label, value):
        path = FIXTURES / f'{name}.json'
        cases = json.loads(path.read_text())
        cases[verdict].append({'name': label, 'value': value})
        write_json(path, cases)
    locator_values = [
        {'kind': 'pdf-page', 'page': 2, 'page_label': 'ii', 'width': 600, 'height': 800, 'rotation': 0, 'coordinate_system': 'top-left-points', 'rectangle': [10, 20, 100, 200]},
        {'kind': 'epub-resource', 'resource': 'chapter1.xhtml', 'reading_order': 0, 'start_offset': 10, 'end_offset': 50},
        {'kind': 'caption-cue', 'lesson_id': 'lesson-1', 'cue_id': 'cue-1', 'start_seconds': 1.25, 'end_seconds': 4.5},
        {'kind': 'code-lines', 'commit': 'a' * 40, 'path': 'src/main.py', 'start_line': 1, 'end_line': 20},
        {'kind': 'legacy-chunk', 'chunk_id': 'old-child', 'parent_id': 'old-parent', 'page_mapping': 'not found'},
    ]
    for value in locator_values:
        add_case('locator', 'valid', value['kind'], value)
    add_case('locator', 'invalid', 'rectangle outside physical page', {**locator_values[0], 'rectangle': [10, 20, 700, 200]})
    add_case('locator', 'invalid', 'reversed EPUB offsets', {**locator_values[1], 'end_offset': 5})
    add_case('locator', 'invalid', 'reversed measured cue time', {**locator_values[2], 'end_seconds': 0.5})
    add_case('evidence-read', 'invalid', 'changed returned evidence bytes', {**evidence, 'content': 'changed'})
    absent = copy.deepcopy(coverage_sample)
    absent['conclusion'] = 'no-indexed-evidence-in-scope'
    absent['certificate']['processing']['state'] = 'failed'
    response_path = FIXTURES / 'response.coverage.json'
    response = json.loads(response_path.read_text())['valid'][0]['value']
    add_case('response.coverage', 'invalid', 'false absence over failed units', {**response, 'data': absent})
    for name in outputs:
        response_path = FIXTURES / f'response.{name}.json'
        value = json.loads(response_path.read_text())['valid'][0]['value']
        unavailable = copy.deepcopy(value)
        unavailable['data'] = None
        unavailable['metadata'].update(backend_availability='unavailable', sources=[], errors=[{
            'code': 'backend_unavailable', 'message': 'Synthetic backend is unavailable', 'retryable': True, 'retry_after_ms': None}])
        add_case('response.' + name, 'valid', 'unavailable optional backend', unavailable)
    new_payload_samples = {
        'stale_flag': {'target': target, 'reason': 'Rechecked synthetic source', 'detected_at': '2026-10-14T00:00:00Z', 'observed_version': 'edition-1', 'resolution': 'Scoped check passed', 'resolved_at': '2026-10-14T01:00:00Z'},
        'tag': {'subject': target, 'label': 'synthetic-tag', 'rationale': 'Synthetic classification'},
        'link': {'subject': target, 'predicate': 'supports', 'object': target, 'rationale': 'Synthetic relation', 'applicability': 'one chapter'},
        'source_change': {'target': target, 'target_hash': 'a' * 64, 'before': 'Before', 'after': 'After', 'rationale': 'Synthetic proposal', 'applied': False},
        'review': {'target': target, 'disposition': 'approve-patch', 'check': {'writer': 'owner', 'writer_assurance': 'authenticated'}, 'scope': 'one chapter'},
    }
    for kind, payload in new_payload_samples.items():
        value = copy.deepcopy(annotation)
        value.update(kind=kind, payload_schema='mind/stale-flag@2' if kind == 'stale_flag' else f'mind/{kind}@1', payload=payload)
        add_case('annotation-record', 'valid', kind, value)
        if kind == 'stale_flag':
            value['payload']['resolved_at'] = None
            add_case('annotation-record', 'invalid', 'closure without time', value)
    print(f'Generated {len(list(SCHEMAS.glob("*.json")))} schemas; {len(tool_index)} tools. Approval pending.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pi-root', type=Path, required=True)
    main(parser.parse_args().pi_root.resolve())
