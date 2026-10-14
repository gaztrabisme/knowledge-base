"""Discriminating evidence/identity and failed-discovery proving cases."""
import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

from knowledge_base.evidence import EvidenceReader
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/fp'))
from build_catalog_fp import build


class CatalogCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.text = 'Frozen evidence with a short final group.\n'
        self.sha = hashlib.sha256(self.text.encode()).hexdigest()
        manifest = b'{"source_id":"book:test","authority":"nonempty frozen fixture"}\n'
        source_hash = hashlib.sha256(manifest).hexdigest()
        source = {'source_id': 'book:test', 'source_revision': 'sha256:' + source_hash,
                  'source_hash': source_hash, 'privacy_scope': 'owner-private', 'derivation': 'derived',
                  'aliases': [{'namespace': 'slug', 'value': 'test'}]}
        (self.root/'registry.json').write_text(json.dumps([source]))
        (self.root/'redirects.json').write_text(json.dumps([
            {'from_id':'older-id','to_id':'test-p0-c0','reason':'fixture identity redirect'}]))
        db = sqlite3.connect(self.root/'catalog.sqlite')
        db.executescript('''CREATE TABLE points(collection,point_id,chunk_id,source_key,parent_id,payload_sha256,payload);
          CREATE TABLE chunks(chunk_id PRIMARY KEY,source_id,role,parent_id,collection,point_id,
            content_sha256,locator,status,reason,text,source_revision,source_hash);
          CREATE TABLE source_manifests(source_id PRIMARY KEY, manifest BLOB);''')
        db.execute('INSERT INTO source_manifests VALUES(?,?)',('book:test',manifest))
        p = {'child_text': self.text}
        raw = json.dumps(p,sort_keys=True,separators=(',',':')).encode()
        db.execute('INSERT INTO points VALUES(?,?,?,?,?,?,?)', ('v10','1','test-p0-c0','test','test-p0',hashlib.sha256(raw).hexdigest(),zlib.compress(raw)))
        self.locator = {'kind':'legacy-chunk','chunk_id':'test-p0-c0','parent_id':'test-p0','page_mapping':'not found'}
        db.execute('INSERT INTO chunks VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
            ('test-p0-c0','book:test','child','test-p0','v10','1',self.sha,json.dumps(self.locator),'not found','locator not found',None,source['source_revision'],source_hash))
        db.commit();db.close()

    def reader(self):
        return EvidenceReader(self.root/'catalog.sqlite', self.root)

    def test_old_chunk_id_same_evidence(self):
        with self.reader() as reader:
            read = reader.read(chunk_id='test-p0-c0')
            self.assertEqual(read['content'], self.text)
            self.assertEqual(read['content_sha256'], self.sha)
            self.assertEqual(read['verification'], 'exact')
            self.assertEqual(read['metadata']['sources'][0]['returned_text_hash'], self.sha)

    def test_unknown_page_stays_not_found(self):
        with self.reader() as reader:
            read = reader.read(source_id='test', locator=self.locator)
            self.assertEqual(read['locator']['page_mapping'],'not found')
            self.assertTrue(read['metadata']['errors'])

    def test_redirect_record_resolves(self):
        with self.reader() as reader:
            self.assertEqual(reader.read(chunk_id='older-id')['content_sha256'],self.sha)

    def test_failed_discovery_never_deletes(self):
        before = (self.root/'catalog.sqlite').read_bytes()
        registry_before = (self.root/'registry.json').read_bytes()
        for _ in range(2):
            with self.assertRaises(ValueError):
                build(self.root/'catalog.sqlite', self.root, self.root/'next-generation')
            self.assertEqual((self.root/'catalog.sqlite').read_bytes(),before)
            self.assertEqual((self.root/'registry.json').read_bytes(),registry_before)
            self.assertFalse((self.root/'next-generation').exists())

    def test_failed_source_discovery_keeps_capture_and_retry_works(self):
        from unittest.mock import patch
        from catalog_io import load as real_load
        path=self.root/'capture.sqlite'
        db=sqlite3.connect(path)
        db.executescript("CREATE TABLE points(collection,point_id,chunk_id,source_key,parent_id,payload_sha256,payload); CREATE TABLE capture(collection,points);")
        payload={'child_id':'test-p0-c0','parent_id':'test-p0','child_text':self.text,'parent_text':self.text,'book_title':'Test'}
        raw=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
        db.execute('INSERT INTO points VALUES(?,?,?,?,?,?,?)',('developer_knowledge_v10','1','test-p0-c0','test','test-p0',hashlib.sha256(raw).hexdigest(),zlib.compress(raw)))
        db.execute('INSERT INTO capture VALUES(?,?)',('developer_knowledge_v10',1))
        db.commit();db.close()
        before=path.read_bytes()
        chunk=self.root/'data/chunks/test.json';chunk.parent.mkdir(parents=True)
        chunk.write_text('{broken source discovery')
        records=self.root/'new-records'
        def fixture_load(p):
            if Path(p).name=='baseline.json':
                return {'remote':{'membership':{'per_source_counts':{'test':1}},'files':{f'gate/v10-{n}.jsonl':{} for n in ('hard','easy','sanity')}}}
            return real_load(p)
        with patch('build_catalog_fp.load',side_effect=fixture_load):
            with self.assertRaises(ValueError):build(path,self.root,records)
            self.assertEqual(path.read_bytes(),before)
            self.assertFalse(records.exists())
            chunk.write_text(json.dumps({'parents':[{'parent_id':'test-p0','text':self.text}],'children':[{'child_id':'test-p0-c0','text':self.text}]}))
            md=self.root/'data/markdown/test.md';md.parent.mkdir(parents=True);md.write_text(self.text)
            original_replace = Path.replace
            def fail_database_swap(src,dst):
                if Path(dst)==path:
                    raise OSError('simulated publication I/O failure')
                return original_replace(src,dst)
            for _ in range(2):
                with patch.object(Path,'replace',fail_database_swap), self.assertRaises(OSError):
                    build(path,self.root,records)
                self.assertEqual(path.read_bytes(),before)
                self.assertFalse(records.exists())
            build(path,self.root,records)
        with EvidenceReader(path,records) as reader:
            self.assertEqual(reader.read(chunk_id='test-p0-c0')['content'],self.text)

    def test_invented_registry_revision_is_rejected(self):
        path=self.root/'registry.json'
        sources=json.loads(path.read_text())
        sources[0]['source_hash']='b'*64
        sources[0]['source_revision']='sha256:'+'b'*64
        path.write_text(json.dumps(sources))
        with self.assertRaises(ValueError):
            self.reader()

    def test_legacy_locator_opens_markdown_mapped_evidence(self):
        db=sqlite3.connect(self.root/'catalog.sqlite')
        loc={'kind':'markdown-lines','path':'data/markdown/test.md','start_line':1,'end_line':2}
        db.execute('UPDATE chunks SET locator=?,status=?',(json.dumps(loc),'mapped'))
        db.commit();db.close()
        with self.reader() as reader:
            self.assertEqual(reader.read(source_id='book:test',locator=self.locator)['content'],self.text)

    def test_returned_locator_roundtrips_when_source_lines_overlap(self):
        db=sqlite3.connect(self.root/'catalog.sqlite')
        locator=json.dumps({'kind':'markdown-lines','path':'test.md','start_line':1,'end_line':1},sort_keys=True,separators=(',',':'))
        db.execute('UPDATE chunks SET locator=?,status=?',(locator,'mapped'))
        old=db.execute('SELECT source_revision,source_hash FROM chunks').fetchone()
        db.execute('INSERT INTO chunks VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
          ('test-p0','book:test','parent','test-p0','v10',None,self.sha,locator,'mapped','source lines',zlib.compress(self.text.encode()),*old))
        db.commit();db.close()
        with self.reader() as reader:
            read=reader.read(chunk_id='test-p0-c0')
            self.assertEqual(read['locator'],self.locator)
            reread=reader.read(source_id=read['source_id'],revision=read['source_revision'],locator=read['locator'])
            self.assertEqual(reread['content_sha256'],read['content_sha256'])

    def test_changed_payload_is_rejected(self):
        db=sqlite3.connect(self.root/'catalog.sqlite')
        db.execute('UPDATE points SET payload=?',(zlib.compress(b'{"child_text":"changed"}'),))
        db.commit();db.close()
        with self.reader() as reader, self.assertRaises(ValueError):
            reader.read(chunk_id='test-p0-c0')

    def test_locator_cannot_attach_to_other_source(self):
        with self.reader() as reader, self.assertRaises(KeyError):
            reader.read(source_id='book:other',locator=self.locator)

    def test_redirect_cycle_rejected(self):
        (self.root/'redirects.json').write_text(json.dumps([{'from_id':'a','to_id':'b'},{'from_id':'b','to_id':'a'}]))
        with self.reader() as reader, self.assertRaises(ValueError):
            reader.read(chunk_id='a')


if __name__ == '__main__':
    unittest.main()
