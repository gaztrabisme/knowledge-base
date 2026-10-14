"""Capture frozen Mac payloads and verified controls into a NEW local staging DB.

Refuses to overwrite an existing database. All Qdrant requests are GET or scroll.
"""
import sqlite3
import sys
import zlib
from pathlib import Path

from catalog_io import ROOT, canonical, digest, load, qdrant, read_remote_file, scroll


def capture(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / 'catalog.sqlite'
    if target.exists():
        raise ValueError('refusing to replace an existing frozen database')
    partial = destination / 'capture.partial.sqlite'
    if partial.exists():
        raise ValueError('incomplete capture exists; preserve it and use a new destination')
    baseline = load(ROOT / 'data/baseline/baseline.json')
    for name in ('hard', 'easy', 'sanity'):
        relative = f'gate/v10-{name}.jsonl'
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(read_remote_file(relative))
    (destination / 'frozen-manifest.json').write_bytes(read_remote_file('frozen/manifest.json'))
    db = sqlite3.connect(partial)
    db.executescript('''
        CREATE TABLE points(collection TEXT, point_id TEXT, chunk_id TEXT UNIQUE,
          source_key TEXT, parent_id TEXT, payload_sha256 TEXT, payload BLOB,
          PRIMARY KEY(collection,point_id));
        CREATE INDEX source_points ON points(source_key);
        CREATE TABLE capture(collection TEXT PRIMARY KEY, points INTEGER);
    ''')
    for collection in ('developer_knowledge_v10', 'philosophy'):
        expected = qdrant(f'collections/{collection}')['points_count']
        if collection == 'developer_knowledge_v10' and expected != baseline['remote']['membership']['points']:
            raise ValueError('v10 count differs from P1')
        count = 0
        for point in scroll(collection):
            p = point['payload']
            key = p['child_id'].rsplit('-p', 1)[0]
            content = canonical(p)
            db.execute('INSERT INTO points VALUES(?,?,?,?,?,?,?)',
                (collection, str(point['id']), p['child_id'], key, p['parent_id'],
                 digest(content), zlib.compress(content)))
            count += 1
            if count % 25000 == 0:
                db.commit()
                print(f'{collection}: {count}/{expected}', flush=True)
        if count != expected or qdrant(f'collections/{collection}')['points_count'] != expected:
            raise ValueError('collection changed during capture')
        db.execute('INSERT INTO capture VALUES(?,?)', (collection, count))
        db.commit()
        print(f'{collection}: captured {count}', flush=True)
    counts = dict(db.execute("SELECT source_key,count(*) FROM points WHERE collection='developer_knowledge_v10' GROUP BY source_key"))
    if counts != baseline['remote']['membership']['per_source_counts']:
        raise ValueError('v10 per-source membership differs from P1')
    db.close()
    partial.rename(target)


if __name__ == '__main__':
    capture(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'data/fp')
