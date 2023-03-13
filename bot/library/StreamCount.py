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
        
        trackid = track.uri[32:]
        if self.db.search(self.q.id == trackid):
            self.db.update(increment('count'), Query().id == trackid)
        else:
            self.db.insert({
                'count': 1,
                'id': trackid,
                'title': track.title,
                'url': track.uri,
                # 'author': track.author
            })

    def get_top_tracks(self, top=5):
        
        all_cnt = self.db.all()

        top = min([len(all_cnt), top, 20])
        top_tracks = heapq.nlargest(top, all_cnt, key=lambda x: x['count'])
        
        return top_tracks
