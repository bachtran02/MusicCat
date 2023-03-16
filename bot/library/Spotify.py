import requests
import random

class Spotify:
    def __init__(self, client_id, client_secret) -> None:
        
        if not (client_id and client_secret):
            raise KeyError
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.s = requests.Session()
        self.token = self.get_access_token(
            self.s,
            client_id=client_id,
            client_secret=client_secret
        )
    
    @staticmethod
    def get_access_token(session, client_id, client_secret):
        
        # requesting new token...
        r = session.post(
            url='https://accounts.spotify.com/api/token',
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        r.raise_for_status()
        return r.json().get('access_token', '')
    
    def get_playlist_tracks(self, playlist_id):
        """Get 10 songs in random order from spotify playlist"""
        
        for i in range(5):

            r = self.s.get(
                url=f'https://api.spotify.com/v1/playlists/{playlist_id}',
                headers = {'Authorization': f"Bearer {self.token}"}
            )
            data = r.json()
            if 'error' in data:
                if data['error'].get('status', None) == 401:  # invalid access / expired token
                    self.token = self.get_access_token(
                        session=self.s,
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                    )
                else:
                    r.raise_for_status()
            else:
                queries = []
                data = r.json()
                tracks = data['tracks']['items']
                random.shuffle(tracks)  # shuffle playlist

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
        raise TimeoutError('Failed to verify credentials')
