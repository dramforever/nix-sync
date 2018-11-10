import requests
import sqlite3
import lzma
import hyper.contrib
import itertools
import json

def parse_narinfo(narinfo):
    res = dict()
    for line in narinfo.splitlines():
        (key, value) = line.split(': ', 1)
        res[key] = value
    return res

class CacheMirror:
    def __init__(self, database, cache_url):
        self.connection = hyper.HTTP20Connection('cache.nixos.org')
        self.database = database
        self.cache_url = cache_url

        self.database.execute('''
            create table if not exists narinfo (
                store_hash text primary key unique,
                narinfo text not null,
                is_complete integer not null default 0
            );''')

        self.database.execute('''
            create table if not exists ref (
                source text not null,
                destination text not null,
                primary key ( source, destination )
            );''')

    def batch_narinfo(self, hashes):
        while True:
            try:
                sids = [
                    self.connection.request('GET', f'{h}.narinfo')
                    for h in hashes ]
                
                def response_text(h, sid):
                    resp = self.connection.get_response(sid)
                    assert resp.status == 200
                    print(f'Downloading {h}')
                    return resp.read().decode()

                responses = [ response_text(h, sid) for h, sid in zip(hashes, sids) ]
                return list(zip(hashes, responses))
            except (AssertionError, hyper.common.exceptions.SocketError) as e:
                print(e)
                print('Retry')
                self.connection.close()
                self.connection = hyper.HTTP20Connection('cache.nixos.org')

    def recursive_get_narinfo(self, todo_hashes):
        CHUNK_SIZE = 64
        todo = todo_hashes

        def get_refs(narinfo):
            refs_str = parse_narinfo(narinfo)['References']
            return (h.split('-', 1)[0] for h in refs_str.split())

        def process(store_hash, narinfo, log=True):
            if log:
                print(f'Processing {store_hash}')
            refs = (
                h
                for h in get_refs(narinfo)
                if h not in visited)
            todo.extend(refs)

        while todo:
            to_download = []
            visited = set()
            while todo and len(to_download) < CHUNK_SIZE:
                next_hash = todo.pop(0)
                if next_hash not in visited:
                    visited.add(next_hash)
                    for is_complete, narinfo in self.database.execute('''
                        select is_complete, narinfo
                        from narinfo
                        where store_hash = ?''', (next_hash,)):
                        if not is_complete:
                            process(next_hash, narinfo, log=False)
                        break
                    else:
                        to_download.append(next_hash)

            narinfos = self.batch_narinfo(to_download)
            self.database.executemany('''
                insert into narinfo (store_hash, narinfo)
                values (?, ?);''', narinfos)
            self.database.executemany('''
                insert into ref (source, destination)
                values (?, ?);''',
                ((store_hash, ref_hash)
                    for store_hash, narinfo in narinfos
                    for ref_hash in get_refs(narinfo)))
            self.database.execute('commit')
            for store_hash, narinfo in narinfos:
                process(store_hash, narinfo)
        self.database.execute('''
            update narinfo
            set is_complete = 1;''')
        self.database.execute('commit')

    def get_channel(self, path):
        with open(path) as pf:
            store_path_file = pf.read()

        store_hashes = [
            store_path.split('/')[3].split('-', 1)[0]
            for store_path in store_path_file.splitlines()]

        self.recursive_get_narinfo(store_hashes)

def download():
    with sqlite3.connect('nix-sync.db') as database:
        cache_mirror = CacheMirror(database, 'https://cache.nixos.org')
        store_path_list = 'store-paths'
        cache_mirror.get_channel(store_path_list)

if __name__ == "__main__":
    print("Undocumented script. Read carefully before using.")
