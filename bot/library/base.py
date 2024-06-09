import re
from random import randrange
import logging

import hikari
import lavalink
from lavalink import LoadType

from bot.utils import format_time
from bot.library.classes.sources import *

URL_RX = re.compile(r'https?://(?:www\.)?.+')

async def _join(bot, guild_id: int, author_id: int):

    states = bot.cache.get_voice_states_view_for_guild(guild_id)
    voice_state = next(filter(lambda i : i[0] == author_id, states.items()), None)
    
    assert voice_state is not None  # should already be covered via checks

    bot.d.lavalink.player_manager.create(guild_id=guild_id)
    try:
        await bot.update_voice_state(guild_id, voice_state[0].channel_id, self_deaf=True)
    except RuntimeError as e:
        logging.error('Failed to join voice channel on guild: %s, Reason: %s', guild_id, e)
        raise e
    logging.info('Client connected to voice channel on guild: %s', guild_id)

async def _get_tracks(lavalink: lavalink.Client, query: str = None, source: Source = YouTube) -> lavalink.LoadResult:
    
    def parse_query(query):
        query = query.strip('<>')
        return query
    
    query = parse_query(query)
    if not URL_RX.match(query):
        query = '{}:{}'.format(source.search_prefix, query)

    result = await lavalink.get_tracks(query)
    if result.load_type == LoadType.PLAYLIST and result.tracks:
        result.tracks[0].user_data['playlist_url'] = query

    return result
        
async def _play(bot, result: lavalink.LoadResult, guild_id: int, author_id: int,
        text_channel: int = 0, play_next: bool = False, loop: bool = False, shuffle: bool = True) -> hikari.Embed:
    
    if not result or result.load_type in (LoadType.ERROR, LoadType.EMPTY):
        logging.warning('Failed to load search result')
        return

    player = bot.d.lavalink.player_manager.get(guild_id)
    if not player or not player.is_connected:
        await _join(bot, guild_id, author_id)
        player = bot.d.lavalink.player_manager.get(guild_id)
    
    result_type, description, image_url, num_tracks = None, None, None, 0
    if result.load_type in (LoadType.TRACK, LoadType.SEARCH):
        result_type, num_tracks = 'track', 1
        track = result.tracks[0]
        player.add(requester=author_id, track=track, index=0 if play_next else None)
        player.set_loop(1) if loop else None
        image_url = track.artwork_url
        description = '[{}]({})\n{} `{}`\n\n<@!{}>'.format(
            track.title, track.uri, track.author,
            'LIVE' if track.stream else format_time(track.duration), 
            track.requester)

    if result.load_type == LoadType.PLAYLIST:
        result_type = 'playlist'
        tracks = result.tracks
        num_tracks = len(tracks)
        if not result.plugin_info or result.plugin_info.get('type') not in ('artist', 'playlist', 'album'):
            playlist_url = tracks[0].user_data.get('playlist_url', None)
            description = 'Playlist [{}]({}) - {} tracks\n\n<@{}>'.format(
                result.playlist_info.name, playlist_url, num_tracks, author_id)
        else:
            plugin_info = result.plugin_info
            result_type = plugin_info.get('type')
            if result_type == 'artist':
                playlist_url, image_url = plugin_info.get('url'), plugin_info.get('artworkUrl')
                description = '[{}]({}) - `{} tracks`\n\n<@{}>'.format(
                    plugin_info.get('author').upper(), playlist_url, num_tracks, author_id)
            elif result_type in ('playlist', 'album'):
                playlist_url, image_url = plugin_info.get('url'), plugin_info.get('artworkUrl')
                description = '[{}]({}) `{} track(s)`\n{}\n\n<@{}>'.format(
                    result.playlist_info.name, playlist_url, num_tracks, plugin_info.get('author'), author_id)
            else:
                raise Exception('Unknown result type!')
        while tracks:
            pop_at = randrange(len(tracks)) if shuffle else 0
            track = tracks.pop(pop_at)
            track.user_data = {
                'playlist_name': result.playlist_info.name,
                'playlist_url': playlist_url,
            }
            player.add(requester=author_id, track=track)
        player.set_loop(2) if loop else None

    player.send_channel = text_channel
    if not player.is_playing:
        await player.play()

    return hikari.Embed(
        title=f'{result_type.capitalize()} added',
        description=description).set_thumbnail(image_url)