import requests
import urllib.parse
import os

def extract_spotify_playlist_id(url):
    parsed_url = urllib.parse.urlparse(url)

    if parsed_url.scheme != "https" or parsed_url.hostname != "open.spotify.com":
        return ""
    if not parsed_url.path.startswith("/playlist/"):
        return ""

    path_parts = parsed_url.path.split("/")
    playlist_id = path_parts[-1]
    return playlist_id

def get_songs_from_spotify_playlist(playlist_id: str):
    
    if not playlist_id:
        raise ValueError("URL to Spotify playlist is invalid")

    r = requests.post(
        url='https://accounts.spotify.com/api/token',
        data={"grant_type": "client_credentials"},
        auth=(os.environ['SPOTIFY_CLIENT_ID'], os.environ['SPOTIFY_CLIENT_SECRET']),
    )

    if r.status_code != 200:
        r.raise_for_status()
        return

    token = r.json()["access_token"]
    r = requests.get(
        url=f'https://api.spotify.com/v1/playlists/{playlist_id}',
        headers = {'Authorization': f"Bearer {token}"}
    )

    if r.status_code != 200:
        raise ValueError("Error while making Spotify API requests")
    
    queries = []
    data = r.json()
    for track in data['tracks']['items']:
        search_query = track['track']['name']
        for artist in track['track']['artists']:
            search_query += ' ' + artist['name']
        queries.append(search_query)

    return queries