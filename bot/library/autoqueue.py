import os
from random import randrange, shuffle
from lavalink.models import AudioTrack

from googleapiclient.discovery import build
from googleapiclient import errors

from bot.constants import BASE_YT_URL

class Autoqueue:

    def __init__(self, client):
        self.client = client
        self.recent_queue = []
        self.yt = self.build_yt_client()
        
    @staticmethod
    def build_yt_client():
        try:
            client = build('youtube', 'v3', static_discovery=False, developerKey=os.environ['YOUTUBE_API_KEY'])
        except Exception as error:
            raise error
        return client

    def get_ytclient(self):
        return self.yt

    async def get_related(self, ytid: str = None):
        
        if not ytid:
            return

        self.recent_queue.append(ytid)
        
        search = self.yt.search().list(
            part='snippet',
            type='video',
            relatedToVideoId=ytid,
            maxResults=10
        ).execute()

        if not search['items']:
            return

        items = search['items']
        shuffle(items)

        related_tracks = []
        i = 0
        for item in items:
            if i == 3:
                break
            itemid = item['id']['videoId']
            if itemid in self.recent_queue:
                continue
            url = f'{BASE_YT_URL}/watch?v={itemid}'
            results = await self.client.get_tracks(url)
            if not results or not results.tracks:
                continue
                
            track = results.tracks[0]
            if track.duration > 600000:  # avoid playing youtube "playlist"
                continue
            related_tracks.append(track)
            i += 1

        return related_tracks
