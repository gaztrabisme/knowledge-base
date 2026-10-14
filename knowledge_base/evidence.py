"""Read immutable FP evidence without loading search models or changing MCP tools."""
import hashlib
import json
import os
import sqlite3
import uuid
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def default_data_dir():
    if os.environ.get('FP_DATA_DIR'):
        return Path(os.environ['FP_DATA_DIR']).expanduser()
    main = Path(os.environ.get('FP_MAIN_CHECKOUT', '/Users/GaryT/Documents/Work/tools/knowledge-base'))
    permanent = main / 'data/fp'
    return permanent if (permanent / 'catalog.sqlite').exists() else ROOT / 'data/fp'


class EvidenceReader:
    """Read-only frozen snapshot. Aliases resolve exactly, ambiguity fails visibly.

    Match tier `exact` means returned UTF-8 bytes match frozen indexed evidence.
    Source locator failures are separately disclosed in metadata; they never replace
    the payload with today's source text. No authorisation service is implemented here.
    """
    def __init__(self, database=None, records=None):
        path = Path(database) if database else default_data_dir() / 'catalog.sqlite'
        self.db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
        self.db.row_factory = sqlite3.Row
        records = Path(records) if records else ROOT / 'data/catalog-fp'
        self.registry = {s['source_id']: s for s in json.loads((records / 'registry.json').read_text())}
        for source in self.registry.values():
            manifest = self.db.execute('SELECT manifest FROM source_manifests WHERE source_id=?', (source['source_id'],)).fetchone()
            if manifest is None or hashlib.sha256(manifest[0]).hexdigest() != source['source_hash'] or source['source_revision'] != 'sha256:' + source['source_hash']:
                self.db.close()
                raise ValueError('registry revision differs from frozen source manifest')
        self.redirects = {r['from_id']: r['to_id'] for r in json.loads((records / 'redirects.json').read_text())}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.db.close()

    def resolve_source(self, name):
        if name in self.registry:
            return name
        matches = {s['source_id'] for s in self.registry.values() for a in s['aliases']
                   if a['value'].casefold() == name.casefold()}
        if len(matches) != 1:
            raise KeyError(f'source not found or ambiguous: {name}; alternatives: {sorted(matches)}')
        return matches.pop()

    def resolve_chunk(self, name):
        seen = set()
        while name in self.redirects:
            if name in seen:
                raise ValueError('redirect cycle')
            seen.add(name)
            name = self.redirects[name]
        row = self.db.execute('SELECT * FROM chunks WHERE chunk_id=?', (name,)).fetchone()
        if row is None:
            raise KeyError(f'chunk not found: {name}')
        return row

    def read(self, *, chunk_id=None, source_id=None, locator=None, revision=None):
        if chunk_id is not None:
            if source_id is not None or locator is not None:
                raise ValueError('supply chunk_id OR source_id and locator')
            row = self.resolve_chunk(chunk_id)
        else:
            if source_id is None or not isinstance(locator, dict):
                raise ValueError('source_id and locator are required')
            source_id = self.resolve_source(source_id)
            if locator.get('kind') == 'legacy-chunk':
                row = self.resolve_chunk(locator.get('chunk_id', ''))
                expected = {'kind':'legacy-chunk','chunk_id':row['chunk_id'],'parent_id':row['parent_id'],'page_mapping':'not found'}
                if row['source_id'] != source_id or expected != locator:
                    raise ValueError('locator is bound to different evidence')
            else:
                key = json.dumps(locator,ensure_ascii=False,sort_keys=True,separators=(',', ':'))
                rows = self.db.execute('SELECT * FROM chunks WHERE source_id=? AND locator=?', (source_id,key)).fetchall()
                if len(rows) != 1:
                    raise KeyError('locator not found or ambiguous; use a legacy chunk locator for an exact span')
                row = rows[0]
        source = self.registry[row['source_id']]
        if row['source_revision'] != source['source_revision'] or row['source_hash'] != source['source_hash']:
            raise ValueError('chunk source revision differs')
        if revision is not None and revision != source['source_revision']:
            raise ValueError('source revision conflict')
        if row['role'] == 'child':
            point = self.db.execute('SELECT payload,payload_sha256 FROM points WHERE collection=? AND point_id=?',
                                    (row['collection'],row['point_id'])).fetchone()
            raw = zlib.decompress(point['payload'])
            if hashlib.sha256(raw).hexdigest() != point['payload_sha256']:
                raise ValueError('frozen payload hash differs')
            content = json.loads(raw)['child_text']
        else:
            content = zlib.decompress(row['text']).decode()
        sha = hashlib.sha256(content.encode()).hexdigest()
        if sha != row['content_sha256']:
            raise ValueError('frozen evidence text hash differs')
        locator = json.loads(row['locator'])
        if locator['kind'] != 'legacy-chunk' and self.db.execute(
                'SELECT count(*) FROM chunks WHERE source_id=? AND locator=?',
                (row['source_id'], row['locator'])).fetchone()[0] > 1:
            # v1 line/page locators lack character offsets. Return an unambiguous
            # preserved selector; the bulk map retains the best source witness.
            locator = {'kind':'legacy-chunk','chunk_id':row['chunk_id'],
                       'parent_id':row['parent_id'],'page_mapping':'not found'}
        snapshot = 'fp-P2:' + row['collection']
        producing = 'frozen-text-sha256:' + sha
        error = [] if row['status'] == 'mapped' else [{
            'code': 'not_found', 'message': row['status'] + ': ' + row['reason'],
            'retryable': False, 'retry_after_ms': None}]
        mapping = {k: source[k] for k in ['source_id','source_revision','source_hash','privacy_scope']}
        mapping.update(producing_revision=producing, returned_text_hash=sha, locator=locator)
        metadata = {'schema_version':'mind-read/v1','read_id':str(uuid.uuid4()),
            'backend_availability':'partial' if error else 'ready', 'source_snapshot':snapshot,
            'index_snapshot':row['collection'],'graph_snapshot':None,'privacy_scope':source['privacy_scope'],
            'sources':[mapping],'legacy_character_truncation':False,'budget_truncation':False,
            'omitted_count':0,'cursor':None,'errors':error,'budget':None}
        return {'schema_version':'mind/evidence-read@1','evidence_id':row['chunk_id'],
            **{k: source[k] for k in ['source_id','source_revision','source_hash','privacy_scope']},
            'selected_snapshot':snapshot,'producing_revision':producing,'locator':locator,
            'content':content,'content_sha256':sha,'derivation':source['derivation'],
            'verification':'exact','annotations':[],'metadata':metadata}


def read_evidence(**kwargs):
    """Convenience function; EvidenceReader is preferred for repeated reads."""
    with EvidenceReader() as reader:
        return reader.read(**kwargs)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument('--chunk-id')
    selector.add_argument('--source-id', help='fixed logical source ID or exact old name')
    parser.add_argument('--locator', help='JSON locator, or @path to a JSON file')
    parser.add_argument('--revision')
    parser.add_argument('--data-dir', type=Path)
    args = parser.parse_args()
    locator = None
    if args.locator:
        value = Path(args.locator[1:]).read_text() if args.locator.startswith('@') else args.locator
        locator = json.loads(value)
    try:
        with EvidenceReader(args.data_dir / 'catalog.sqlite' if args.data_dir else None) as reader:
            result = reader.read(chunk_id=args.chunk_id,source_id=args.source_id,locator=locator,revision=args.revision)
    except (KeyError,ValueError,OSError,sqlite3.Error) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
