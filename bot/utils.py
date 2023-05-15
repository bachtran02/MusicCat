import urllib.parse
import lavalink
import typing as t

def parse_time(time: int) -> t.Tuple[int, int, int, int]:
    """
    Parses the given time into days, hours, minutes and seconds.
    Useful for formatting time yourself.

    Parameters
    ----------
    time: :class:`int`
        The time in milliseconds.

    Returns
    -------
    Tuple[:class:`int`, :class:`int`, :class:`int`, :class:`int`]
    """
    days, remainder = divmod(time / 1000, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    return days, hours, minutes, seconds

def format_time(time: int, option: str = 'a') -> str:
    
    days, hours, minutes, seconds = parse_time(time)

    if option == 'a':
        if days:
            option = 'd'
        elif hours:
            option = 'h'
        else:
            option = 'm'
        
    if option == 'd':
        return '%d:%02d:%02d:%02d' % (days, hours, minutes, seconds)
    elif option == 'h':
        return '%d:%02d:%02d' % (days * 24 + hours, minutes, seconds)
    elif option == 'm':
        return '%d:%02d' % ((days * 24 + hours) * 60 + minutes, seconds)

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
        playtime = f'{format_time(player.position)} | {format_time(player.current.duration)}'
        bar = progress_bar(player.position/player.current.duration)

    return f'{play_emj} {bar} `{playtime}` {loop_emj}{shuffle_emj} \n'

def transform_string(string:str = '', max_length:int = -1):
    
    if not string or max_length == -1:
        return
    
    