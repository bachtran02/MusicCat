from lavalink.models import (DeferredAudioTrack, LoadResult, LoadType, PlaylistInfo, Source)
import typing as t
import random
from bot.constants import BASE_YT_URL

class LoadError(Exception):
    pass

# source to search and access Spotify playlists only
class lnchillSource(Source):
    def __init__(self):
        super().__init__(name='linhnhichill')

    async def load_item(self, client, query: str = None, use_source: bool = False) -> t.Optional[LoadResult]:
        
        # prevent source from being used out of use case
        if not use_source:  
            return None

        query = f'{BASE_YT_URL}/playlist?list=PL-F2EKRbzrNQte4aGjHp9cQau9peyPMw0'
        result =  await client.get_tracks(query=query, check_local=False)
        if not result.load_type == 'PLAYLIST_LOADED':
            return LoadResult(LoadType.NO_MATCHES, tracks=[], playlist_info=None)
        
        selected_track = random.randrange(len(result['tracks']))
        return LoadResult(LoadType.TRACK, tracks=[result.tracks[selected_track]], playlist_info=None)
