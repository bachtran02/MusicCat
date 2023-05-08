from lavalink.models import (DeferredAudioTrack, LoadResult, LoadType, PlaylistInfo, Source)
import urllib.parse
import requests
import typing as t

class LoadError(Exception):
    pass

class SpotifyTrack(DeferredAudioTrack):

    async def load(self, client):  # Load our 'actual' playback track using the metadata from this one.
        result: LoadResult = await client.get_tracks('ytsearch:{0.title} {0.author}'.format(self))  # Search for our track on YouTube.

        if result.load_type != LoadType.SEARCH or not result.tracks:  # We're expecting a 'SEARCH' due to our 'ytsearch' prefix above.
            raise LoadError

        first_track = result.tracks[0]  # Grab the first track from the results.
        
        # update metadata
        self.identifier = first_track.identifier
        self.duration = first_track.duration
        self.uri = first_track.uri

        base64 = first_track.track  # Extract the base64 string from the track.
        self.track = base64  # We'll store this for later, as it allows us to save making network requests

        return base64

# source to search and access Spotify playlists only
class SpofitySource(Source):
    def __init__(self, client_id: str = None, client_secret: str = None):
        super().__init__(name='spotify')
        
        self._client_id = client_id
        self._client_secret = client_secret
        self._token = None

    @staticmethod
    def parse_spotify_playlist_id(query: str = None):

        parsed_url = urllib.parse.urlparse(query)

        if parsed_url.scheme != "https" or parsed_url.hostname != "open.spotify.com" \
            or not parsed_url.path.startswith("/playlist/"):
            return None  # not spotify playlist

        path_parts = parsed_url.path.split("/")
        return path_parts[-1]
    
    def refresh_access_token(self):
        
        r = requests.post(
            url='https://accounts.spotify.com/api/token',
            data={"grant_type": "client_credentials"},
            auth=(self._client_id, self._client_secret),
        )
        res = r.json()
        self._token = res.get('access_token', None)
    
    def make_api_request(self, url, query=None, is_retry: bool = False):

        if not self._token:
            self.refresh_access_token()

        r = requests.get(
            url=f'https://api.spotify.com/v1/{url}',
            headers = {'Authorization': f"Bearer {self._token}"}
        )

        if r.status_code == 401 and not is_retry:
            self._token = None
            return self.make_api_request(url, query, is_retry=True)
        
        return r.json() if r.status_code == 200 else None
    
    def get_playlist_tracks(self, playlist_id: str = None) -> t.Optional[t.Tuple]:

        data = self.make_api_request(url=f'playlists/{playlist_id}')
        return (data['name'], data['tracks']['items']) if data else None  # playlist name, tracks

    async def load_item(self, client, query: str) -> t.Optional[LoadResult]:

        if not (playlist_id := self.parse_spotify_playlist_id(query)):
            return None

        if not (playlist := self.get_playlist_tracks(playlist_id)):
            return None

        playlist_tracks = []
        for item in playlist[1]:
            track_info = item['track']
            
            track = SpotifyTrack(data={
                'identifier': track_info['id'],
                'isSeekable': True,
                'author': ', '.join([artist['name'] for artist in track_info['artists']]),
                'length': track_info['duration_ms'],
                'isStream': False,
                'title': track_info['name'],
                'uri': track_info['external_urls'].get('spotify', None),
            }, requester=0),
            playlist_tracks.append(track[0])

        return LoadResult(LoadType.PLAYLIST, playlist_tracks, playlist_info=PlaylistInfo(name=playlist[0]))
