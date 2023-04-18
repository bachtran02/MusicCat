import urllib.parse
import lavalink

def get_spotify_playlist_id(url: str):

    parsed_url = urllib.parse.urlparse(url)

    if parsed_url.scheme != "https" or parsed_url.hostname != "open.spotify.com":
        return (False, None)
    if not parsed_url.path.startswith("/playlist/"):
        return (False, None)

    path_parts = parsed_url.path.split("/")
    return (True, path_parts[-1])

def convert_ms(ms: int) -> str:

    ms = round(ms)
    total_seconds = ms // 1000

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return (hours, minutes, seconds)

def duration_str(duration: int) -> str:
    
    time = convert_ms(duration)
    timestr = f'{time[0]}:{time[1]:02}' if time[0] else f'{time[1]}'
    timestr += f':{time[2]:02}'

    return timestr

def progress_bar(percent: float) -> str:

    str = ''
    for i in range(12):
        if i == (int)(percent*12):
            str+='🔘'
        else:
            str+='▬'
    return str;

def player_bar(player: lavalink.DefaultPlayer):

    loop_emj = ''
    if player.loop == player.LOOP_SINGLE:
        loop_emj = '🔂 '
    elif player.loop == player.LOOP_QUEUE:
        loop_emj = '🔁 '

    play_emj = '▶️' if not player.paused else '⏸️'
    shuffle_emj = '🔀 ' if player.shuffle else ''

    if player.current.stream:
        playtime = 'LIVE'
        bar = progress_bar(0.99)
    else:
        playtime = f'{duration_str(player.position)} | {duration_str(player.current.duration)}'
        bar = progress_bar(player.position/player.current.duration)

    return f'{play_emj} {bar} `{playtime}` {loop_emj}{shuffle_emj} \n'