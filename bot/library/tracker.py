import heapq
import lavalink
from tinydb import TinyDB, Query
from tinydb.operations import increment

class StreamCount:
    def __init__(self) -> None:
        self.db = TinyDB(
            'logs/stream_data.json', 
            encoding='utf-8',
        )
        self.q = Query()

    def handle_stream(self, track: lavalink.AudioTrack):
        
        if self.db.search(self.q.id == track.identifier):
            self.db.update(increment('count'), Query().id == track.identifier)
        else:
            self.db.insert({
                'count': 1,
                'id': track.identifier,
                'title': track.title,
                'url': track.uri,
                # 'author': track.author
            })

    def get_top_tracks(self, top=5):
        
        all_cnt = self.db.all()

        top = min([len(all_cnt), top, 20])
        top_tracks = heapq.nlargest(top, all_cnt, key=lambda x: x['count'])
        
        return top_tracks
