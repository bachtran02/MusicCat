import re
import logging
import hikari
from lavalink.models import AudioTrack
from typing import Optional, Union, List, Dict

from bot.utils import get_spotify_playlist_id
from bot.constants import COLOR_DICT

async def _join(bot, guild_id: int, author_id: int):
    
    assert guild_id is not None

    states = bot.cache.get_voice_states_view_for_guild(guild_id)
    voice_state = [state[1] for state in filter(lambda i : i[0] == author_id, states.items())]
    channel_id = voice_state[0].channel_id

    try:
        await bot.update_voice_state(guild_id, channel_id, self_deaf=True)
        player = bot.d.lavalink.player_manager.create(guild_id=guild_id)
    except TimeoutError as error:
        raise TimeoutError('Unable to connect to the voice channel!') from error
    
    logging.info('Client connected to voice channel on guild: %s', guild_id)
    return channel_id


async def _search(lavalink, spotify, query=None) -> Optional[Union[AudioTrack, Dict]]:
    
    query = query.strip('<>')  # <url> to suppress embed on Discord

    [is_spotify_playlist, playlist_id] = get_spotify_playlist_id(query)
    if is_spotify_playlist:  # Spotify playlist
        if not spotify:
            return None

        tracks = []
        playlist = spotify.get_playlist_tracks(playlist_id)

        for track in playlist['tracks']:
            trackq = f'ytsearch: {track} audio'
            results = await lavalink.get_tracks(trackq)
            track.append(results.tracks[0])
        return {
            'playlist': {
                'name': playlist['name'],
                'url': query,
            'tracks': tracks
            }
        }

    else:
        url_rx = re.compile(r'https?://(?:www\.)?.+')
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results = await lavalink.get_tracks(query)

        if not results or not results.tracks:
            raise error
        
        if results.load_type == 'PLAYLIST_LOADED':  # YouTube playlist
            tracks = results.tracks
            
            return {
                'playlist': {
                    'name': results.playlist_info.name,
                    'url': query,
                },
                'tracks': results.tracks
            }
        else:  # YouTube track url or title
            return results.tracks[0]

# TODO: index to track to queue
async def _play(bot, guild_id: int, author_id: int, query: str,
        textchannel: int = 0, loop: bool = False, autoplay: str = 'None'):

    if not query:
        return

    result = await _search(
        lavalink=bot.d.lavalink,
        spotify=bot.d.spotify,
        query=query,
    )

    if not result:
        return
    
    embed = hikari.Embed(color=COLOR_DICT['GREEN'])
    
    player = bot.d.lavalink.player_manager.get(guild_id)
    if not player or not player.is_connected:
        await _join(bot, guild_id, author_id)
        player = bot.d.lavalink.player_manager.get(guild_id)

    if isinstance(result, dict):  # playlist
        for track in result['tracks']:
            player.add(requester=author_id, track=track)
        if loop:
            player.set_loop(2)
        embed.description = f'Playlist [{result["playlist"]["name"]}]({result["playlist"]["url"]})' \
            f'- {len(result["tracks"])} tracks added to queue <@{author_id}>'
    else:
        player.add(requester=author_id, track=result)
        if loop:
            player.set_loop(1)
        embed.description = f'[{result.title}]({result.uri}) added to queue <@{author_id}>'

    if not player.is_playing:
        await player.play()

    if autoplay == 'True':
        player.is_autoplay = True
    elif autoplay == ' False':
        player.is_autoplay = False

    player.textchannel_id = textchannel
    
    return embed
    