import requests
import random
import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

class Spotify:
    def __init__(self, client_id, client_secret) -> None:
        
        if not (client_id and client_secret):
            raise KeyError
        
        self.client_id = client_id
        self.client_secret = client_secret

        self.update_token()

        # run job to update spotify access token on interval
        sched = BackgroundScheduler(daemon=True)
        sched.add_job(self.update_token, CronTrigger(hour='*'))
        sched.start()

    @staticmethod
    def get_access_token(client_id, client_secret):
        
        r = requests.post(
            url='https://accounts.spotify.com/api/token',
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        r.raise_for_status()
        res = r.json()
        return res.get('access_token', '')
    
    def update_token(self):
        try:
            self.token = self.get_access_token(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
        except requests.HTTPError as error:
            raise TimeoutError('Failed to verify credentials') from error
            
    def get_playlist_tracks(self, playlist_id):
        """Get 10 songs in random order from spotify playlist"""

        r = requests.get(
            url=f'https://api.spotify.com/v1/playlists/{playlist_id}',
            headers = {'Authorization': f"Bearer {self.token}"}
        )
        r.raise_for_status()
        data = r.json()
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
    