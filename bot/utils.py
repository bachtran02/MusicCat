import requests
import urllib.parse
import os

class MusicCommandError(Exception):
    pass

def get_spotify_playlist_id(url: str):

    parsed_url = urllib.parse.urlparse(url)

    if parsed_url.scheme != "https" or parsed_url.hostname != "open.spotify.com":
        return None
    if not parsed_url.path.startswith("/playlist/"):
        return None

    path_parts = parsed_url.path.split("/")
    return path_parts[-1]
