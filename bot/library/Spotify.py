import requests
import random

class Spotify:
    def __init__(self, client_id, client_secret) -> None:

        if not (client_id and client_secret):
            raise KeyError

        self.s = requests.Session()
        self.token = self.get_access_token(
            self.s,
            client_id=client_id,
            client_secret=client_secret
        )
    
    @staticmethod
    def get_access_token(session, client_id, client_secret):
        
        r = session.post(
            url='https://accounts.spotify.com/api/token',
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        r.raise_for_status()

        return r.json().get('access_token', '')
    
    def get_playlist_tracks(self, playlist_id):
        """Get 10 songs in random order from spotify playlist"""

        while True: 
            try:
                r = self.s.get(
                    url=f'https://api.spotify.com/v1/playlists/{playlist_id}',
                    headers = {'Authorization': f"Bearer {self.token}"}
                )
            except requests.HTTPError as e:
                raise e

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
                    
                return {
                    'name': data['name'],
                    'tracks': queries
                }
