"""Build registry/locators from captured payloads and observed source witnesses.

No changes to live search, source bytes or frozen points. Incomplete discovery is
never reconciled as deletion. New small records are staged then validated before
publishing; a prior generation may not be overwritten.
"""
import argparse
import datetime
import json
import re
import shutil
import sqlite3
import tempfile
import zlib
from collections import Counter
from pathlib import Path

from catalog_io import MAIN, RECORDS, ROOT, canonical, digest, file_hash, load, write
from validate_contracts import Contracts

UNKNOWN = {'value': None, 'reason': 'not found'}
DEFECTS = ['dropped_short_final_group', 'repeated_heading_suffixes']


def assert_discovery(expected, actual):
    if not actual or expected != actual:
        raise ValueError('failed discovery: previous membership must be preserved')


def known(value):
    return {'value': value, 'reason': None}


def stage(state, expected=None, attempted=None, completed=None, errors=(), profile=None):
    return {'state':state,'expected':known(expected) if expected is not None else UNKNOWN,
        'attempted':known(attempted) if attempted is not None else UNKNOWN,
        'completed':known(completed) if completed is not None else UNKNOWN,
        'profile':profile,'errors':list(errors)}


def natural_id(value):
    match = re.search(r'-p(\d+)(?:-c(\d+))?$', value)
    return tuple(int(x or -1) for x in match.groups()) if match else (value,)


class SourceWitness:
    def __init__(self, source_key, collection, main):
        self.main = Path(main)
        prefix = 'philosophy/' if collection == 'philosophy' else ''
        self.md_path = f'data/markdown/{prefix}{source_key}.md'
        self.chunk_path = f'data/chunks/{prefix}{source_key}.json'
        self.files = []
        for name in (self.md_path,self.chunk_path):
            path = self.main / name
            if path.is_file():
                self.files.append({'backend':'main-checkout','path':name,'sha256':file_hash(path),'bytes':path.stat().st_size})
        chunk_file = self.main / self.chunk_path
        chunks = load(chunk_file) if chunk_file.exists() else {}
        self.children = {c['child_id']:c for c in chunks.get('children',[])}
        self.parents = {p['parent_id']:p for p in chunks.get('parents',[])}
        path = self.main / self.md_path
        self.md = path.read_text() if path.exists() else None
        self.normal = re.sub(r'\s+', ' ', self.md).strip() if self.md is not None else None
        self.norm_line_starts = None

    def locate(self, text, chunk_id, parent_id, role):
        local = (self.children if role == 'child' else self.parents).get(chunk_id)
        fallback = {'kind':'legacy-chunk','chunk_id':chunk_id,'parent_id':parent_id,'page_mapping':'not found'}
        if local is None:
            return fallback, 'not found', 'locator not found: chunk ID is missing from current source chunks'
        if local['text'] != text:
            return fallback, 'drifted', 'source drifted: current chunk text differs from frozen Qdrant payload'
        if self.md is None:
            return fallback, 'not found', 'locator not found: Markdown file is missing'
        # Exact normalized contiguous matching is a location witness, never a quote substitution.
        target = re.sub(r'\s+', ' ', text).strip()
        pos = self.normal.find(target) if target else -1
        if pos < 0 or self.normal.find(target,pos+1) >= 0:
            return fallback, 'mapped', 'legacy locator retained: unique Markdown correspondence not found; page mapping not found'
        if self.norm_line_starts is None:
            # Build offsets using the same global whitespace normalization, not line-by-line joins.
            self.norm_line_starts = []
            line = 1
            for match in re.finditer(r'\S+|\s+',self.md):
                token = match.group()
                if token.isspace():
                    self.norm_line_starts.append(line)
                    line += token.count('\n')
                else:
                    self.norm_line_starts.extend([line]*len(token))
            # strip() removes at most the leading collapsed whitespace character.
            if self.md and self.md[0].isspace():
                self.norm_line_starts = self.norm_line_starts[1:]
        return {'kind':'markdown-lines','path':self.md_path,
            'start_line':self.norm_line_starts[pos],'end_line':self.norm_line_starts[pos+len(target)-1]}, 'mapped', 'whitespace-normalized contiguous source correspondence; PDF/EPUB page mapping not found'


def bind_revisions(db, registry):
    """Every bulk map row explicitly carries its immutable producing source revision."""
    db.execute('ALTER TABLE chunks ADD COLUMN source_revision TEXT')
    db.execute('ALTER TABLE chunks ADD COLUMN source_hash TEXT')
    for source in registry:
        db.execute('UPDATE chunks SET source_revision=?,source_hash=? WHERE source_id=?',
                   (source['source_revision'],source['source_hash'],source['source_id']))
    db.commit()


def _build_staged(database, main=MAIN, records=RECORDS):
    database,records = Path(database),Path(records)
    if (records/'registry.json').exists():
        raise ValueError('refusing to overwrite a catalog generation; stage in a new records directory')
    db = sqlite3.connect(database)
    db.row_factory = sqlite3.Row
    expected = load(ROOT/'data/baseline/baseline.json')['remote']['membership']['per_source_counts']
    actual = dict(db.execute("SELECT source_key,count(*) FROM points WHERE collection='developer_knowledge_v10' GROUP BY source_key"))
    assert_discovery(expected,actual)  # BEFORE creating tables or replacing any records.
    if db.execute("SELECT name FROM sqlite_master WHERE name='chunks'").fetchone():
        raise ValueError('map already built; preserve existing generation')
    db.executescript('''CREATE TABLE chunks(chunk_id TEXT PRIMARY KEY,source_id TEXT,role TEXT,
      parent_id TEXT,collection TEXT,point_id TEXT,content_sha256 TEXT,locator TEXT,status TEXT,reason TEXT,text BLOB);
      CREATE INDEX source_chunks ON chunks(source_id,locator);
      CREATE TABLE source_manifests(source_id TEXT PRIMARY KEY, manifest BLOB);
    ''')
    staging = Path(tempfile.mkdtemp(prefix='catalog-records-', dir=records.parent))
    contracts = Contracts()
    captured_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    config_text = (ROOT/'knowledge_base/config.py').read_text()
    import ast
    tree = ast.parse(config_text)
    book_names = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='BOOKS' for t in n.targets))
    registry,catalog,manifests,source_counts = [],[],[],[]
    for collection,key,count in db.execute('SELECT collection,source_key,count(*) FROM points GROUP BY collection,source_key ORDER BY collection,source_key').fetchall():
        source_id = ('book:' if collection != 'philosophy' else 'philosophy:') + key
        witness = SourceWitness(key,collection,main)
        rows = db.execute('SELECT * FROM points WHERE source_key=? ORDER BY chunk_id',(key,)).fetchall()
        parent_texts = {}
        titles = set()
        stats = Counter()
        point_parent_drift = 0
        for row in rows:
            p = json.loads(zlib.decompress(row['payload']))
            titles.add(p['book_title'])
            pid = p['parent_id']
            if pid in parent_texts and parent_texts[pid] != p['parent_text']:
                raise ValueError(f'conflicting frozen parent evidence: {pid}')
            parent_texts[pid] = p['parent_text']
            if pid in witness.parents and witness.parents[pid]['text'] != p['parent_text']:
                point_parent_drift += 1
            locator,status,reason = witness.locate(p['child_text'],row['chunk_id'],pid,'child')
            stats['child_'+status] += 1
            db.execute('INSERT INTO chunks VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                (row['chunk_id'],source_id,'child',pid,collection,row['point_id'],digest(p['child_text'].encode()),canonical(locator).decode(),status,reason,None))
        for pid,text in sorted(parent_texts.items(),key=lambda kv:natural_id(kv[0])):
            locator,status,reason = witness.locate(text,pid,pid,'parent')
            stats['parent_'+status] += 1
            db.execute('INSERT INTO chunks VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                (pid,source_id,'parent',pid,collection,None,digest(text.encode()),canonical(locator).decode(),status,reason,zlib.compress(text.encode())))
        # Revision identity hashes the exact frozen payload inventory plus observed witnesses.
        inventory_hash = digest(canonical([[r['point_id'],r['chunk_id'],r['payload_sha256']] for r in rows]))
        manifest = {'schema_version':'mind/frozen-source-manifest@1','source_id':source_id,
            'collection':collection,'source_key':key,'frozen_payload_inventory_sha256':inventory_hash,
            'child_count':count,'parent_count':len(parent_texts),'files':witness.files,
            'edition':UNKNOWN,'publication_date':UNKNOWN,'revision_date':UNKNOWN,'original_acquired_at':UNKNOWN,
            'original_asset':UNKNOWN,'page_mapping':UNKNOWN,
            'reasons':{'edition':'No verified edition-to-frozen-payload binding was found.',
            'dates':'No verified publication, revision or original acquisition date was found.',
            'original_asset':'Requested main Library contains no book assets. Normalized files are separate observed witnesses.',
            'page_mapping':'No verified physical page or EPUB-resource offset mapping exists for this frozen generation.'},
            'authority':'Frozen Mac Qdrant payload, including drifted/missing-source text; current source files are locator witnesses only.'}
        raw = canonical(manifest) + b'\n'
        source_hash = digest(raw)
        revision_path = 'revisions/' + key + '.json'
        write(staging/revision_path,manifest)
        manifests.append({'source_id':source_id,'path':revision_path,'sha256':source_hash})
        db.execute('INSERT INTO source_manifests VALUES(?,?)',(source_id,raw))
        aliases = [{'namespace':'slug','value':key}]
        names = titles | ({book_names[key]} if key in book_names else set())
        if collection == 'philosophy':
            aliases.append({'namespace':'work-id','value':key.rsplit('.',1)[0]})
        aliases.extend({'namespace':'book-title','value':x} for x in sorted(names))
        source = {'schema_version':'mind/source@1','source_id':source_id,'source_revision':'sha256:'+source_hash,
            'source_hash':source_hash,'privacy_scope':'owner-private','kind':'book','aliases':aliases,
            'canonical_url':None,'title':book_names.get(key,sorted(titles)[0]),'creators':[],
            'publication_date':UNKNOWN,'revision_date':UNKNOWN,'acquired_at':captured_at,
            'selected_scope':f'Frozen indexed text in {collection}; {count} children and {len(parent_texts)} parents',
            'derivation':'derived'}
        registry.append(source)
        errors = [f'{k}: {v}' for k,v in sorted(stats.items()) if k.endswith(('not found','drifted'))]
        entry = {'schema_version':'mind/catalog-entry@1','source':source,'snapshot':'fp-P2:'+collection,
            'ordered_membership':sorted(parent_texts,key=natural_id),'inventory_complete':True,
            'archive':stage('completed',count,count,count,profile='frozen-qdrant-payload-archive/v1'),
            'parse':stage('pending',errors=['Historical parse receipts and expected original source units: not found']),
            'index':stage('completed',count,count,count,profile=collection),
            'extraction':stage('pending',errors=['No extraction receipt for this frozen scope: not found']),
            'omitted_modalities':['image','audio','video'],'truncation':False,'quote_checks':'not found',
            'gaps':errors+['Original-asset archive and parse completeness: not found. inventory_complete applies only to frozen indexed parent membership.',
            'Known defects preserved: dropped short final group; repeated heading suffixes.',
            'Historical truncation extent and exact quote checks: not found.']}
        contracts.validate('source-identity',source)
        contracts.validate('catalog-entry',entry)
        catalog.append(entry)
        source_counts.append({'source_id':source_id,'collection':collection,'source_key':key,
            'children':count,'parents':len(parent_texts),'counts':dict(stats),
            'point_parent_text_differences':point_parent_drift,
            'source_children_excluded':len(set(witness.children)-{r['chunk_id'] for r in rows})})
        db.commit()
        if len(registry)%40==0: print(f'mapped {len(registry)} sources',flush=True)
    collections = {}
    for collection,n in db.execute('SELECT * FROM capture'):
        selected = [s for s in source_counts if s['collection']==collection]
        counts = Counter()
        for s in selected:counts.update(s['counts'])
        collections[collection] = {'points':n,'sources':len(selected),'parents':sum(s['parents'] for s in selected),'counts':dict(counts),
            'point_parent_text_differences':sum(s['point_parent_text_differences'] for s in selected),
            'source_children_excluded':sum(s['source_children_excluded'] for s in selected)}
    write(staging/'registry.json',registry)
    # One file per source keeps individual git records reviewable.
    for entry in catalog:write(staging/'catalog'/ (entry['source']['source_id'].replace(':','_')+'.json'),entry)
    write(staging/'source-manifests.json',manifests)
    write(staging/'ledger.json',{'schema_version':'mind/catalog-ledger@1','collections':collections,'sources':source_counts,
        'redirected':0,'known_content_defects':DEFECTS,'count_units':{
            'points':'child Qdrant points','ordered_membership':'frozen indexed parents; numeric legacy order',
            'archive':'frozen child payloads preserved, independent of original-asset archive',
            'parse/extraction':'historical receipts unavailable; null is not zero'},
        'facts_not_found':['original edition binding','publication/revision/original acquisition dates','PDF/EPUB page mapping','original-asset archive completeness','historical truncation extent']})
    write(staging/'redirects.json',[])
    write(staging/'storage.json',{'schema_version':'mind/catalog-storage@1','permanent_home':str(MAIN/'data/fp'),
        'database':'catalog.sqlite','tables':dict(db.execute("SELECT 'points',count(*) FROM points UNION ALL SELECT 'chunks',count(*) FROM chunks UNION ALL SELECT 'source_manifests',count(*) FROM source_manifests")),
        'sha256':None,'controls':{f'gate/v10-{name}.jsonl':load(ROOT/'data/baseline/baseline.json')['remote']['files'][f'gate/v10-{name}.jsonl'] for name in ('hard','easy','sanity')}})
    bind_revisions(db, registry)
    db.execute('VACUUM')
    db.close()
    storage = load(staging/'storage.json');storage['sha256']=file_hash(database);storage['bytes']=database.stat().st_size
    write(staging/'storage.json',storage)
    # Keep helper docs/schemas, but never silently delete membership records.
    records.mkdir(parents=True,exist_ok=True)
    for path in staging.iterdir():shutil.move(str(path),str(records/path.name))
    staging.rmdir()
    print(f'built {len(registry)} sources; {database}',flush=True)


def build(database, main=MAIN, records=RECORDS):
    """Build in isolation. Any discovery/parse/validation failure keeps capture intact."""
    database, records = Path(database), Path(records)
    if (records/'registry.json').exists():
        raise ValueError('refusing to replace an existing catalog generation')
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as original:
        expected = load(ROOT/'data/baseline/baseline.json')['remote']['membership']['per_source_counts']
        actual = dict(original.execute("SELECT source_key,count(*) FROM points WHERE collection='developer_knowledge_v10' GROUP BY source_key"))
        assert_discovery(expected,actual)
        if original.execute("SELECT name FROM sqlite_master WHERE name='chunks'").fetchone():
            raise ValueError('map already built; preserve existing generation')
        before = file_hash(database)
        with tempfile.TemporaryDirectory(prefix='.catalog-build-',dir=database.parent) as task_dir:
            task_dir = Path(task_dir)
            staged_db = task_dir/'catalog.sqlite'
            with sqlite3.connect(staged_db) as staged:
                original.backup(staged)
            staged_records = task_dir/'records'
            _build_staged(staged_db,main,staged_records)
            if file_hash(database) != before:
                raise ValueError('capture changed while building; no generation published')
            if any((records/p.name).exists() for p in staged_records.iterdir()):
                raise ValueError('record destination conflict; no generation published')
            # Publish the complete small-record directory in one rename. Restore it
            # if the final database swap fails; never leave a partial registry visible.
            previous_records = task_dir/'previous-records'
            had_records = records.exists()
            if had_records:
                shutil.copytree(records,staged_records,dirs_exist_ok=True)
            records.parent.mkdir(parents=True,exist_ok=True)
            published = False
            moved_previous = False
            try:
                if had_records:
                    records.rename(previous_records)
                    moved_previous = True
                staged_records.replace(records)
                published = True
                staged_db.replace(database)
            except OSError:
                if published:
                    records.rename(task_dir/'failed-records')
                if moved_previous:
                    previous_records.rename(records)
                raise


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,default=ROOT/'data/fp/catalog.sqlite')
    parser.add_argument('--main-checkout',type=Path,default=MAIN)
    parser.add_argument('--records',type=Path,default=RECORDS)
    args=parser.parse_args()
    build(args.database,args.main_checkout,args.records)
