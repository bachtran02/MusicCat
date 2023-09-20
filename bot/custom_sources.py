"""
from lavalink import (LoadResult, LoadType, Source, LoadResult)
import typing as t
import random
import requests
from bot.constants import BASE_YT_URL

class LoadError(Exception):
    pass

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

"""