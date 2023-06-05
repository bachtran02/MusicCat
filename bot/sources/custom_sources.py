from typing import Any, Optional
from lavalink import (DeferredAudioTrack, LoadResult, LoadType, Source, Client, LoadResult)
import typing as t
import random
import requests
from bot.constants import BASE_YT_URL

# from bot.fixture import Fixture

class LoadError(Exception):
    pass

# source to search and access Spotify playlists only
class lnchillSource(Source):
    def __init__(self, token: str = None):
        super().__init__(name='linhnhichill')
        self._token = token

    def get_channel_latest(self, params: dict =None):

        params['key'] = self._token
        r = requests.get(
            url='https://www.googleapis.com/youtube/v3/search',
            params=params,
        )
        return r.json() if r.status_code == 200 else None

    async def load_item(self, client, query: str = None, use_source: bool = False) -> t.Optional[LoadResult]:
        
        # prevent source from being used out of use case
        if not use_source:  
            return None
        
        url = f'{BASE_YT_URL}/playlist?list=PL-F2EKRbzrNQte4aGjHp9cQau9peyPMw0'
        if self._token and query.split(':')[-1] == 'latest':
            params = {
                'part': 'snippet',
                'channelId': 'UCOGDtlp0av6Cp366BGS_PLQ',
                'maxResults': 10,
                'order': 'date', 
            }
            if (res := self.get_channel_latest(params=params)):
                vid_id = res.get('items', [])[0].get('id', {}).get('videoId', None)
                url = f'{BASE_YT_URL}/watch?v={vid_id}'
                
        result =  await client.get_tracks(query=url, check_local=False)
        if result.load_type in (LoadType.PLAYLIST, LoadType.TRACK):
            selected_track = random.randrange(len(result['tracks'])) if result.load_type == LoadType.PLAYLIST else 0
            return LoadResult(LoadType.TRACK, tracks=[result.tracks[selected_track]], playlist_info=None)
        return LoadResult(LoadType.NO_MATCHES, tracks=[], playlist_info=None)


# class talkSportStream(DeferredAudioTrack):

#     def __init__(self, data: dict, requester: int = 0, stream_url : str = None, **extra):
#         super().__init__(data, requester, **extra)
#         self.stream_url = stream_url

#     async def load(self, client):
        
#         # search for track using isrc
#         result: LoadResult = await client.get_tracks(query=self.stream_url)
#         if result.load_type != LoadType.TRACK or not result.tracks:
#             raise LoadError

#         first_track = result.tracks[0] 

#         base64 = first_track.track  
#         self.track = base64

#         return base64


# class talkSportSource(Source):
#     def __init__(self):
#         super().__init__(name='talkSport')
    
#     async def load_item(self, client, query: Fixture = None, use_source: bool = False) -> t.Optional[LoadResult]:

#         if not use_source:
#             return None
        
#         result = [talkSportStream(
#             data={
#                 'identifier': query.fid,
#                 'isSeekable': False,
#                 'author': 'talkSPORT',
#                 'length': 0x7FFFFFFFFFFFFFFF,  # stream never expires
#                 'isStream': True,
#                 'title': query.title,
#                 'uri': query.url,
#                 'isrc': None,
#             },
#             requester=0,
#             stream_url=query.stream_url
#         )]
#         return LoadResult(LoadType.TRACK, result, playlist_info=None)
