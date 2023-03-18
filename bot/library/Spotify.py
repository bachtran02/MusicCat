import requests
import random
import time
import threading

class Spotify:
    def __init__(self, client_id, client_secret) -> None:
        
        if not (client_id and client_secret):
            raise KeyError
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.s = requests.Session()

        self.token = self.get_access_token(
            self.s,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        self._thread = None
        self.start_token_thread()

    @staticmethod
    def get_access_token(session, client_id, client_secret):
        
        r = session.post(
            url='https://accounts.spotify.com/api/token',
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        r.raise_for_status()
        res = r.json()
        return res.get('access_token', '')
    
    def start_token_thread(self):

        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self.update_token)
            self._thread.start()
    
    def update_token(self):

        while True:
            try:
                self.token = self.get_access_token(
                    self.s,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
            except requests.HTTPError as error:
                raise TimeoutError('Failed to verify credentials') from error
            time.sleep(3500)  # ~ one hour interval
            
    def get_playlist_tracks(self, playlist_id):
        """Get 10 songs in random order from spotify playlist"""

        r = self.s.get(
            url=f'https://api.spotify.com/v1/playlists/{playlist_id}',
            headers = {'Authorization': f"Bearer {self.token}"}
        )
        data = r.json()
        # handle errors
        tracks = data['tracks']['items']
        random.shuffle(tracks)  # shuffle playlist
        queries = []
        for j, track in enumerate(tracks):
            if j == 10:
                break

            search_query = track['track']['name']
            for artist in track['track']['artists']:
                search_query += ' ' + artist['name']
            queries.append(search_query)
            
        return {
            'name': data['name'],
            'tracks': queries
        }
    
    def search(self, query: str, qtype='track'):

        r = self.s.get(
            url=f'https://api.spotify.com/v1/search?q={query}&type={qtype}',
            headers = {'Authorization': f"Bearer {self.token}"}
        )
        data = r.json()
        # handle errors
        if not ('tracks' in data and 'items' in data['tracks']):
            return None 
        
        track = data['tracks']['items'][0]
        # if track['type'] != 'track': # make sure search result is a track
        #     return None
        return track

    
    def get_related(self, spotify_id: str):

        if not spotify_id:
            return None
        
        r = self.s.get(
            url=f'https://api.spotify.com/v1/recommendations?seed_tracks={spotify_id}',
            headers = {'Authorization': f"Bearer {self.token}"}
        )

        data = r.json()
        track = data['tracks'][0]
        return track

