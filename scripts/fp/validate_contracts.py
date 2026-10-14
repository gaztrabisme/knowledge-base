"""Offline JSON Schema validator and structural cross-field checks for FP v1.

Requires jsonschema==4.23.0 (see requirements.txt). No model imports/network.
Schema validation cannot prove authorization, transactional durability or real locators;
those require the downstream service checks named in CONTRACTS.md.
"""
import argparse
import json
import hashlib
import sys
from pathlib import Path

from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'data/baseline'


def semantic_errors(value):
    errors = []
    if isinstance(value, list):
        for item in value:
            errors.extend(semantic_errors(item))
    if not isinstance(value, dict):
        return errors
    for start, end in [('start_line', 'end_line'), ('start_offset', 'end_offset'), ('start_seconds', 'end_seconds')]:
        if start in value and end in value and isinstance(value[start], (int, float)) and isinstance(value[end], (int, float)):
            if value[end] < value[start]:
                errors.append(f'{end} precedes {start}')
    if value.get('kind') == 'pdf-page' and isinstance(value.get('rectangle'), list):
        x0, y0, x1, y1 = value['rectangle'] if len(value['rectangle']) == 4 else [0, 0, -1, -1]
        if not all(isinstance(x, (int, float)) for x in [x0, y0, x1, y1]):
            errors.append('rectangle coordinates must be numbers')
        elif not (0 <= x0 <= x1 <= value.get('width', 0) and 0 <= y0 <= y1 <= value.get('height', 0)):
            errors.append('rectangle escapes page or is reversed')
    if value.get('schema_version') == 'mind/evidence-read@1' and isinstance(value.get('content'), str):
        digest = hashlib.sha256(value['content'].encode()).hexdigest()
        if digest != value.get('content_sha256'):
            errors.append('evidence content hash differs')
        metadata = value.get('metadata', {})
        required_mapping = {key: value.get(key) for key in ['source_id', 'source_revision', 'source_hash', 'privacy_scope', 'producing_revision', 'locator']}
        required_mapping['returned_text_hash'] = digest
        if required_mapping not in metadata.get('sources', []):
            errors.append('evidence metadata does not map the same source revision, locator and returned-text hash')
        if metadata.get('source_snapshot') != value.get('selected_snapshot') or metadata.get('privacy_scope') != value.get('privacy_scope'):
            errors.append('evidence snapshot/privacy differs from metadata')
    if isinstance(value.get('legacy_output'), str):
        metadata = value.get('metadata', value.get('_meta', {}).get('mind', {}))
        sources = metadata.get('sources', [])
        if len(sources) == 1 and sources[0].get('returned_text_hash') != hashlib.sha256(value['legacy_output'].encode()).hexdigest():
            errors.append('legacy string differs from its captured returned-text hash')
    if 'read_id' in value and 'metadata' in value and value['read_id'] != value['metadata'].get('read_id'):
        errors.append('read_id differs from pinned metadata')
    if value.get('kind') == 'stale_flag' and value.get('payload_schema') == 'mind/stale-flag@2':
        payload = value.get('payload', {})
        if (payload.get('resolution') is None) != (payload.get('resolved_at') is None):
            errors.append('stale resolution and resolved_at must be present together')
    if all(key in value for key in ['state', 'expected', 'attempted', 'completed']):
        counts = {key: value[key].get('value') for key in ['expected', 'attempted', 'completed'] if isinstance(value[key], dict)}
        if value['state'] in ['completed', 'valid-empty'] and (counts.get('expected') is None or counts.get('completed') != counts.get('expected')):
            errors.append('completed stage requires known, matching expected/completed membership')
        if all(isinstance(counts.get(key), int) for key in ['expected', 'attempted', 'completed']):
            if not 0 <= counts['completed'] <= counts['attempted'] <= counts['expected']:
                errors.append('stage unit counts are inconsistent')
    if value.get('schema_version') == 'mind-tool-response/v1' and value.get('data') is None:
        metadata = value.get('metadata', {})
        if metadata.get('backend_availability') == 'ready' and not metadata.get('errors'):
            errors.append('null result needs unavailable state or explicit error')
    if 'selector' in value and 'target' in value:
        selector, target = value['selector'], value['target']
        if isinstance(selector, dict) and isinstance(target, dict) and target.get('target_type') == 'source':
            if selector.get('source_id') != target.get('target_id') or selector.get('source_revision') != target.get('target_revision'):
                errors.append('selector is bound to a different source revision')
    conclusion = value.get('conclusion', value.get('absence_state'))
    if conclusion in ['no-indexed-evidence-in-scope', 'confirmed-library-gap']:
        certificate = value.get('certificate', {})
        stage = certificate.get('processing', {})
        required_count = len(certificate.get('required_units', []))
        if any(stage.get(key, {}).get('value') != required_count for key in ['expected', 'completed']):
            errors.append('absence processing counts must account for every required unit')
        if stage.get('state') not in ['completed', 'valid-empty'] or certificate.get('omissions'):
            errors.append('incomplete scope cannot assert absence')
        if conclusion == 'confirmed-library-gap' and certificate.get('review_state') != 'checked':
            errors.append('confirmed gap requires original-source review')
    if value.get('schema_version') == 'mind/tested-release@1':
        if any(row.get('verdict') == 'verified' and not row.get('receipt') for row in value.get('installation_matrix', [])):
            errors.append('verified installation row requires a receipt')
        if any(row.get('state') == 'verified' and not row.get('evidence') for row in value.get('capabilities', [])):
            errors.append('verified capability requires evidence')
    if value.get('schema_version') == 'mind/tested-release@1' and value.get('deployment_state') in ['tested', 'released']:
        if value.get('pending_gates') or not value.get('data_parts'):
            errors.append('tested/released set needs data parts and no pending gates')
        if any(row.get('verdict') != 'verified' for row in value.get('installation_matrix', [])) or any(row.get('state') == 'pending' for row in value.get('capabilities', [])):
            errors.append('tested/released set has unfinished installation/capability coverage')
        if not any(x.get('verdict') == 'verified' and x.get('receipt') for x in value.get('installation_matrix', [])):
            errors.append('tested/released set needs verified installation receipts')
    for child in value.values():
        errors.extend(semantic_errors(child))
    return errors


class Contracts:
    def __init__(self, base=BASE):
        self.base = Path(base)
        self.schemas = {}
        registry = Registry()
        for path in sorted((self.base / 'contracts/v1').glob('*.json')):
            schema = json.loads(path.read_text())
            validator_for(schema).check_schema(schema)
            if schema['$id'] in [s['$id'] for s in self.schemas.values()]:
                raise ValueError(f'duplicate schema ID: {path.name}')
            self.schemas[path.stem] = schema
            registry = registry.with_resource(schema['$id'], Resource.from_contents(schema))
        if not self.schemas:
            raise ValueError('empty schema pack')
        self.validators = {name: validator_for(schema)(schema, registry=registry, format_checker=FormatChecker())
                           for name, schema in self.schemas.items()}
        # Resolve every reference even if no fixture reaches its branch. No network retrieval.
        def check_refs(node):
            if isinstance(node, dict):
                if '$ref' in node:
                    registry.resolver().lookup(node['$ref'])
                for child in node.values():
                    check_refs(child)
            elif isinstance(node, list):
                for child in node:
                    check_refs(child)
        for schema in self.schemas.values():
            check_refs(schema)

    def errors(self, name, value):
        structural = [f'{list(error.absolute_path)}: {error.message}'
                      for error in self.validators[name].iter_errors(value)]
        return structural or semantic_errors(value)

    def validate(self, name, value):
        errors = self.errors(name, value)
        if errors:
            raise ValueError(f'{name}: {errors[0]}')

    def fixtures(self):
        count = 0
        paths = {p.stem: p for p in (self.base / 'fixtures/v1').glob('*.json')}
        if set(paths) != set(self.schemas):
            raise ValueError('fixtures must cover exactly every schema')
        for name, path in sorted(paths.items()):
            cases = json.loads(path.read_text())
            if not cases.get('valid') or not cases.get('invalid'):
                raise ValueError(f'{name}: needs positive and negative fixtures')
            for verdict in ['valid', 'invalid']:
                for case in cases[verdict]:
                    errors = self.errors(name, case['value'])
                    if bool(errors) != (verdict == 'invalid'):
                        raise ValueError(f'{name}/{case["name"]}: expected {verdict}; {errors[:1]}')
                    count += 1
        registry = json.loads((self.base / 'tools-v1.json').read_text())
        names = [entry['name'] for entry in registry['tools']]
        if len(names) != 32 or len(set(names)) != len(names):
            raise ValueError('design requires exactly 32 unique tools')
        for tool in registry['tools']:
            for direction in ['request', 'response']:
                if Path(tool[direction]).stem not in self.schemas:
                    raise ValueError(f'missing {direction} schema for {tool["name"]}')
        return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--schema', help='schema filename stem')
    parser.add_argument('--instance', type=Path)
    args = parser.parse_args()
    pack = Contracts(args.base)
    if args.schema or args.instance:
        if not args.schema or not args.instance:
            parser.error('--schema and --instance are required together')
        pack.validate(args.schema, json.loads(args.instance.read_text()))
        print(f'PASS: {args.schema}: {args.instance}')
    else:
        count = pack.fixtures()
        print(f'PASS: {len(pack.schemas)} schemas, 32 tool pairs, {count} positive/negative fixtures')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(1)
