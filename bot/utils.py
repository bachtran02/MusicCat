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
    
def format_track_duration(track: lavalink.AudioTrack):
    return '`LIVE`' if track.stream else format_time(track.duration)

def progress_bar(percent: float) -> str:

    bar = ''
    for i in range(12):
        if i == (int)(percent*12):
            bar += '🔘'
        else:
            bar += '▬'
    return bar;

def player_bar(player: lavalink.DefaultPlayer):

    EMOJIS = {
        'LOOP_TRACK':       '🔂',
        'LOOP_QUEUE':       '🔁',
        'PLAYER_PLAY':      '⏸️',
        'PLAYER_PAUSED':    '▶️',
        'PLAYER_SHUFFLE':   '🔀',
    }

    loop_emoji, playtime, player_bar = '', '', ''
    if player.current.stream:
        playtime = 'LIVE'
        player_bar = progress_bar(0.99)
    else:
        playtime = f'{format_time(player.position)} | {format_time(player.current.duration)}'
        player_bar = progress_bar(player.position/player.current.duration)
    if player.loop == player.LOOP_SINGLE:
        loop_emoji = EMOJIS['LOOP_TRACK']
    elif player.loop == player.LOOP_QUEUE:
        loop_emoji = EMOJIS['LOOP_QUEUE']

    return '{0} {1} `{2}` {3}{4}'.format(
        EMOJIS['PLAYER_PAUSED'] if player.paused else EMOJIS['PLAYER_PLAY'],
        player_bar,
        playtime,
        loop_emoji,
        EMOJIS['PLAYER_SHUFFLE'] if player.shuffle else '',
    )
