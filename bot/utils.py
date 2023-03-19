import urllib.parse

def get_spotify_playlist_id(url: str):

    parsed_url = urllib.parse.urlparse(url)

    if parsed_url.scheme != "https" or parsed_url.hostname != "open.spotify.com":
        return None
    if not parsed_url.path.startswith("/playlist/"):
        return None

    path_parts = parsed_url.path.split("/")
    return path_parts[-1]

def convert_ms(ms) -> str:

    ms = round(ms)
    total_seconds = ms // 1000

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return (hours, minutes, seconds)

def duration_str(duration):
    
    time = convert_ms(duration)
    timestr = f'{time[0]}:{time[1]:02}' if time[0] else f'{time[1]}'
    timestr += f':{time[2]:02}'

    return timestr
