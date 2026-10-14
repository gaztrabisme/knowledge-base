"""Connected exhaustive FP catalog acceptance, with no offline-success bypass."""
import json
import sqlite3
import sys
import zlib
from collections import Counter

from catalog_io import MAIN, RECORDS, ROOT, canonical, connect, control_bytes, data_dir, digest, file_hash, load, qdrant, scroll
from frozen_control_evidence import frozen_control_evidence
from validate_contracts import Contracts

sys.path.insert(0,str(ROOT))
from knowledge_base.evidence import EvidenceReader


def require(condition, message):
    if not condition:raise ValueError(message)


def check():
    print('FP catalog data: '+str(data_dir().resolve()),flush=True)
    print('FP source witnesses: '+str(MAIN.resolve()),flush=True)
    storage=load(RECORDS/'storage.json');database=data_dir()/storage['database']
    require(database.stat().st_size==storage['bytes'] and file_hash(database)==storage['sha256'],'large map hash/size differs')
    print('PASS: large map SHA-256 and byte count',flush=True)
    db=connect(database)
    require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity failed')
    for table,count in storage['tables'].items():
        require(table in ('points','chunks','source_manifests'),'unknown table')
        require(db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]==count,'map row counts differ')
    from jsonschema import Draft202012Validator
    manifest_validator=Draft202012Validator(load(RECORDS/'schemas/frozen-source-manifest.json'))
    redirect_validator=Draft202012Validator(load(RECORDS/'schemas/redirects.json'))
    redirect_validator.validate(load(RECORDS/'redirects.json'))
    contracts=Contracts();registry=load(RECORDS/'registry.json');sources={s['source_id']:s for s in registry}
    require(len(sources)==len(registry),'duplicate source ID')
    ledger=load(RECORDS/'ledger.json')
    require(set(ledger['collections'])=={'developer_knowledge_v10','philosophy'},'required collection ledger missing')
    require(set(dict(db.execute('SELECT * FROM capture')))==set(ledger['collections']),'capture collection inventory differs')
    require(set(sources)=={s['source_id'] for s in ledger['sources']},'source ledger membership differs')
    manifests={m['source_id']:m for m in load(RECORDS/'source-manifests.json')}
    catalog={}
    source_files={}
    for source in registry:
        contracts.validate('source-identity',source)
        sid=source['source_id'];ref=manifests[sid]
        raw=(RECORDS/ref['path']).read_bytes();manifest=json.loads(raw)
        manifest_validator.validate(manifest)
        require(manifest['source_id']==sid,'manifest logical ID differs')
        inventory=[[r['point_id'],r['chunk_id'],r['payload_sha256']] for r in db.execute('SELECT point_id,chunk_id,payload_sha256 FROM points WHERE source_key=? ORDER BY chunk_id',(manifest['source_key'],))]
        require(digest(canonical(inventory))==manifest['frozen_payload_inventory_sha256'],'source payload inventory hash differs')
        require(len(inventory)==manifest['child_count'],'source manifest child count differs')
        require(db.execute("SELECT count(*) FROM chunks WHERE source_id=? AND role='parent'",(sid,)).fetchone()[0]==manifest['parent_count'],'source manifest parent count differs')
        require(digest(raw)==ref['sha256']==source['source_hash'],'source revision hash differs')
        require(source['source_revision']=='sha256:'+source['source_hash'],'revision differs')
        require(db.execute('SELECT manifest FROM source_manifests WHERE source_id=?',(sid,)).fetchone()[0]==raw,'DB source revision differs')
        # Unknown facts may not be filled by filename/title/page-like text inference.
        for field in ('edition','publication_date','revision_date','original_acquired_at','original_asset','page_mapping'):
            require(manifest[field]=={'value':None,'reason':'not found'},'unknown fact was filled: '+field)
        require(source['publication_date']==manifest['publication_date'] and source['revision_date']==manifest['revision_date'],'date fact differs')
        for file in manifest['files']:
            path=MAIN/file['path']
            require(not path.is_symlink() and path.resolve().is_relative_to(MAIN.resolve()),'source path escapes checkout')
            require(path.stat().st_size==file['bytes'] and file_hash(path)==file['sha256'],'source witness hash differs: '+file['path'])
        file=RECORDS/'catalog'/(sid.replace(':','_')+'.json')
        entry=load(file);contracts.validate('catalog-entry',entry)
        require(entry['source']==source,'catalog source differs')
        parents=[r[0] for r in db.execute("SELECT chunk_id FROM chunks WHERE source_id=? AND role='parent'",(sid,))]
        require(set(entry['ordered_membership'])==set(parents) and len(entry['ordered_membership'])==len(parents),'catalog parent membership differs')
        order=lambda x:int(x.rsplit('-p',1)[1])
        require(entry['ordered_membership']==sorted(parents,key=order),'catalog parent order differs')
        require(entry['archive']['profile']=='frozen-qdrant-payload-archive/v1','archive completion scope differs')
        for stage in ('parse','extraction'):
            require(entry[stage]['state']=='pending' and all(entry[stage][x]=={'value':None,'reason':'not found'} for x in ('expected','attempted','completed')),'unknown stage converted to success or zero')
        require(entry['quote_checks']=='not found','unverified quote checks claimed')
        catalog[sid]=entry
        prefix='philosophy/' if manifest['collection']=='philosophy' else ''
        chunk_file=MAIN/f"data/chunks/{prefix}{manifest['source_key']}.json"
        data=load(chunk_file) if chunk_file.exists() else {}
        md=MAIN/f"data/markdown/{prefix}{manifest['source_key']}.md"
        source_files[sid]=(data,md)
    require(len(list((RECORDS/'catalog').glob('*.json')))==len(sources),'extra catalog entry')
    print(f'PASS: {len(registry)} v1 sources/catalog entries, revision manifests and source-file hashes',flush=True)
    # Validate every locator and frozen text, and independently check the named source lines.
    source_counts={};excluded_counts={};child_hashes={};parent_hashes={}
    import re
    normalize=lambda s:re.sub(r'\s+',' ',s).strip()
    for sid,(data,md) in source_files.items():
        locals_by_id={c['child_id']:c['text'] for c in data.get('children',[])}
        locals_by_id.update({p['parent_id']:p['text'] for p in data.get('parents',[])})
        lines=md.read_text().split('\n') if md.exists() else []
        stats=Counter()
        for row in db.execute('SELECT * FROM chunks WHERE source_id=?',(sid,)):
            require(row['source_revision']==sources[sid]['source_revision'] and row['source_hash']==sources[sid]['source_hash'],'map source revision differs')
            loc=json.loads(row['locator']);contracts.validate('locator',loc)
            if row['role']=='child':
                p=db.execute('SELECT payload,payload_sha256,chunk_id,parent_id,source_key,collection FROM points WHERE collection=? AND point_id=?',(row['collection'],row['point_id'])).fetchone()
                require(p is not None and p['chunk_id']==row['chunk_id'] and p['parent_id']==row['parent_id'],'child map differs from point')
                require(sid==('philosophy:' if p['collection']=='philosophy' else 'book:')+p['source_key'],'child map logical source differs')
                raw=zlib.decompress(p['payload']);require(digest(raw)==p['payload_sha256'],'payload blob hash differs')
                content=json.loads(raw)['child_text'];child_hashes[row['chunk_id']]=row['content_sha256']
            else:
                require(row['role']=='parent' and row['parent_id']==row['chunk_id'],'invalid parent map')
                content=zlib.decompress(row['text']).decode();parent_hashes[row['chunk_id']]=row['content_sha256']
            require(digest(content.encode())==row['content_sha256'],'chunk text hash differs')
            require(row['status'] in ('mapped','not found','drifted'),'unknown ledger status')
            if row['status']=='drifted':require(row['chunk_id'] in locals_by_id and content!=locals_by_id[row['chunk_id']],'false source drift')
            elif row['status']=='not found':require(row['chunk_id'] not in locals_by_id or not md.exists(),'false missing locator')
            else:require(locals_by_id.get(row['chunk_id'])==content and md.exists(),'mapped source evidence differs')
            if loc['kind']=='markdown-lines':
                require(row['status']=='mapped' and loc['path']==str(md.relative_to(MAIN)),'Markdown locator source differs')
                require(1<=loc['start_line']<=loc['end_line']<=len(lines),'Markdown locator out of range')
                require(normalize(content) in normalize('\n'.join(lines[loc['start_line']-1:loc['end_line']])),'locator lines do not contain evidence: '+row['chunk_id'])
            else:
                require(loc['kind']=='legacy-chunk' and loc['chunk_id']==row['chunk_id'] and loc['parent_id']==row['parent_id'] and loc['page_mapping']=='not found','unverified physical page was filled')
            stats[row['role']+'_'+row['status']]+=1
        source_counts[sid]=dict(stats)
        frozen_ids={r[0] for r in db.execute("SELECT chunk_id FROM chunks WHERE source_id=? AND role='child'",(sid,))}
        excluded_counts[sid]=len({c['child_id'] for c in data.get('children',[])}-frozen_ids)
        count=sum(v for k,v in stats.items() if k.startswith('child_'))
        for stage in ('archive','index'):
            require(all(catalog[sid][stage][x]['value']==count for x in ('expected','attempted','completed')),'stage counts differ')
    print(f'PASS: all {len(child_hashes)+len(parent_hashes)} child/parent locators and evidence hashes',flush=True)
    for row in ledger['sources']:
        require(row['source_id']==('philosophy:' if row['collection']=='philosophy' else 'book:')+row['source_key'],'ledger logical source differs')
        require(row['source_children_excluded']==excluded_counts[row['source_id']],'excluded child count differs')
        require(row['counts']==source_counts[row['source_id']],'per-source ledger differs')
        require(row['children']==sum(v for k,v in row['counts'].items() if k.startswith('child_')) and row['parents']==sum(v for k,v in row['counts'].items() if k.startswith('parent_')),'source counts differ')
    baseline=load(ROOT/'data/baseline/baseline.json')
    for collection,record in ledger['collections'].items():
        members=[s for s in ledger['sources'] if s['collection']==collection]
        actual=Counter()
        for s in members:actual.update(source_counts[s['source_id']])
        require(db.execute('SELECT points FROM capture WHERE collection=?',(collection,)).fetchone()[0]==record['points'],'capture/ledger point count differs')
        require(dict(actual)==record['counts'],'collection ledger differs')
        require(sum(s['children'] for s in members)==record['points'] and sum(s['parents'] for s in members)==record['parents'] and len(members)==record['sources'],'ledger totals differ')
        require(record['source_children_excluded']==sum(s['source_children_excluded'] for s in members),'excluded child summary differs')
        require(record['point_parent_text_differences']==sum(s['point_parent_text_differences'] for s in members),'parent drift summary differs')
        expected_points=record['points']
        require(qdrant(f'collections/{collection}')['points_count']==expected_points,'Qdrant population changed')
        seen=set();counts=Counter();parent_differences=Counter()
        for point in scroll(collection):
            pid=str(point['id']);require(pid not in seen,'duplicate live point ID');seen.add(pid)
            captured=db.execute('SELECT * FROM points WHERE collection=? AND point_id=?',(collection,pid)).fetchone()
            require(captured is not None,'live point absent from map')
            p=point['payload'];require(digest(canonical(p))==captured['payload_sha256'],'live payload differs from frozen capture')
            require(child_hashes[p['child_id']]==digest(p['child_text'].encode()),'old child text differs')
            require(parent_hashes[p['parent_id']]==digest(p['parent_text'].encode()),'old parent text differs')
            counts[captured['source_key']]+=1
            sid=('philosophy:' if collection=='philosophy' else 'book:')+captured['source_key']
            parents={x['parent_id']:x['text'] for x in source_files[sid][0].get('parents',[])}
            if p['parent_id'] in parents and parents[p['parent_id']]!=p['parent_text']:parent_differences[sid]+=1
            if len(seen)%50000==0:print(f'verified {collection}: {len(seen)}/{expected_points}',flush=True)
        require(len(seen)==expected_points==db.execute('SELECT count(*) FROM points WHERE collection=?',(collection,)).fetchone()[0],'point-map bijection differs')
        require(qdrant(f'collections/{collection}')['points_count']==expected_points,'collection changed during check')
        if collection=='developer_knowledge_v10':
            require(counts==baseline['remote']['membership']['per_source_counts'],'P1 membership differs')
            require(record['points']==330778 and record['sources']==328,'v10 totals differ')
        for row in members:require(parent_differences[row['source_id']]==row['point_parent_text_differences'],'parent drift point count differs')
        print(f'PASS: {collection}, {len(seen)} live point IDs exactly once with identical payloads',flush=True)
    print('PASS: ledger counts reconcile',flush=True)
    frozen=frozen_control_evidence();hit_count=0
    with EvidenceReader(database,RECORDS) as reader:
        for name in ('hard','easy','sanity'):
            rows=[json.loads(line) for line in control_bytes(name).splitlines()]
            for query in rows:
                for hit in query['candidates']:
                    read=reader.read(chunk_id=hit['parent_id']);contracts.validate('evidence-read',read)
                    roundtrip=reader.read(source_id=read['source_id'],locator=read['locator'],revision=read['source_revision'])
                    require(roundtrip['content_sha256']==read['content_sha256'],'returned locator cannot reopen the same evidence')
                    require(read['content_sha256']==frozen[hit['parent_id']]['parent_sha256'],'old hit opens different bppc frozen evidence')
                    require(digest(hit['snippet'].encode()) in frozen[hit['parent_id']]['snippet_sha256'],'control snippet does not match frozen child evidence')
                    hit_count+=1
            print(f'PASS: every {name} control hit opens identical frozen v10 evidence ({len(rows)} queries)',flush=True)
        redirects=load(RECORDS/'redirects.json')
        require(len({r['from_id'] for r in redirects})==len(redirects),'duplicate redirect IDs')
        for redirect in redirects:
            require(db.execute('SELECT 1 FROM chunks WHERE chunk_id=?',(redirect['from_id'],)).fetchone() is None,'redirect shadows preserved old ID')
            reader.read(chunk_id=redirect['from_id'])
    require(ledger['redirected']==len(load(RECORDS/'redirects.json')),'redirect ledger differs')
    require(set(ledger['known_content_defects'])=={'dropped_short_final_group','repeated_heading_suffixes'},'content defects omitted')
    db.close()
    # Run nonempty failure/redirect proving fixtures on every acceptance invocation.
    import subprocess
    subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-p','test_fp_catalog.py'],cwd=ROOT,check=True)
    print(f'PASS: catalog acceptance; {hit_count} frozen control hits',flush=True)


if __name__=='__main__':
    try:check()
    except (ValueError,KeyError,OSError,sqlite3.Error) as error:
        print('FAIL: '+str(error),file=sys.stderr)
        sys.exit(1)
