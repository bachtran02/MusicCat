import lavalink
import typing as t

from bot.constants import EMOJI_RADIO_BUTTON, EMOJI_RESUME_PLAYER, EMOJI_PAUSE_PLAYER

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

def format_time(time: int, option: str = None) -> str:
    
    days, hours, minutes, seconds = parse_time(time)

    if days and (option == 'd' or not option):
        return '%d:%02d:%02d:%02d' % (days, hours, minutes, seconds)
    elif hours and (option == 'h' or not option):
        return '%d:%02d:%02d' % (days * 24 + hours, minutes, seconds)
    return '%d:%02d' % ((days * 24 + hours) * 60 + minutes, seconds)

def progress_bar(percent: float) -> str:

    bar = [EMOJI_RADIO_BUTTON if i == (int)(percent*12) else '▬' for i in range(12)]
    return ''.join(bar);

def player_bar(player: lavalink.DefaultPlayer):

    play_pause = EMOJI_RESUME_PLAYER if player.paused else EMOJI_PAUSE_PLAYER
    if player.current.stream:
        playtime = 'LIVE'
        player_bar = progress_bar(0.99)
    else:
        playtime = f'{format_time(player.position)} | {format_time(player.current.duration)}'
        player_bar = progress_bar(player.position/player.current.duration)

    return f'{play_pause} {player_bar} `{playtime}`'


def trim(s: str, max_len: int) -> str:
    if len(s) > max_len:
        return s[:max_len - 3] + '...'
    return s
