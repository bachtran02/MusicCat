import urllib.parse

COLOR_DICT = {
    'RED': 0xd25557,
    'BLUE': 0x00E7FF ,
    'YELLOW': 0xf9c62b,
    'GREEN': 0x76ffa1,
}

def get_spotify_playlist_id(url: str):

    parsed_url = urllib.parse.urlparse(url)

    if parsed_url.scheme != "https" or parsed_url.hostname != "open.spotify.com":
        return None
    if not parsed_url.path.startswith("/playlist/"):
        return None

    path_parts = parsed_url.path.split("/")
    return path_parts[-1]

def str_from_duration(duration: int):  # duration in ms

    length = divmod(duration, 60000)
    return f'{int(length[0])}:{round(length[1]/1000):02}'
