import urllib
import requests
import os
import random

class SpotifyClient:
    def __init__(self) -> None:
        self.s = requests.Session()
        self.token = self.get_access_token(
            os.environ['SPOTIFY_CLIENT_ID'],
            os.environ['SPOTIFY_CLIENT_SECRET']
        )

    @staticmethod
    def get_playlist_id(url: str):

        parsed_url = urllib.parse.urlparse(url)

        if parsed_url.scheme != "https" or parsed_url.hostname != "open.spotify.com":
            return ""
        if not parsed_url.path.startswith("/playlist/"):
            return ""

        path_parts = parsed_url.path.split("/")
        playlist_id = path_parts[-1]
        
        return playlist_id
    
    @staticmethod
    def get_access_token(client_id, client_secret):
        
        r = requests.post(
            url='https://accounts.spotify.com/api/token',
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        r.raise_for_status()

        return r.json().get('access_token', '')
    
    def get_tracks_from_playlist(self, playlist_id):
        """Get 10 songs in random order from spotify playlist"""

        while True: 
            r = self.s.get(
                url=f'https://api.spotify.com/v1/playlists/{playlist_id}',
                headers = {'Authorization': f"Bearer {self.token}"}
            )

            data = r.json()
            if 'error' in data:
                if data['error'] == '401':
                    self.token = self.get_access_token()
                else:
                    r.raise_for_status()
            else:
                queries = []
                data = r.json()
                tracks = data['tracks']['items']
                random.shuffle(tracks)  # shuffle playlist
                i = 0
                for track in tracks:
                    search_query = track['track']['name']
                    for artist in track['track']['artists']:
                        search_query += ' ' + artist['name']
                    queries.append(search_query)

                    i += 1
                    if i == 10:
                        break
                    
                return queries
