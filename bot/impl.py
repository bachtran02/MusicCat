import re
import logging
from random import randrange
import hikari
import lavalink
from lavalink import LoadType

from bot.constants import COLOR_DICT
from bot.library.datastore import GuildDataStore
from bot.utils import format_time

URL_RX = re.compile(r'https?://(?:www\.)?.+')

async def _join(bot, guild_id: int, author_id: int):

    states = bot.cache.get_voice_states_view_for_guild(guild_id)
    voice_state = [state[1] for state in filter(lambda i : i[0] == author_id, states.items())]
    channel_id = voice_state[0].channel_id  # voice channel user is in

    bot.d.lavalink.player_manager.create(guild_id=guild_id)
    bot.d.guilds[guild_id] = GuildDataStore()
    try:
        await bot.update_voice_state(guild_id, channel_id, self_deaf=True)
    except RuntimeError as e:
        logging.error('Failed to join voice channel on guild: %s, Reason: %s', guild_id, e)
        raise e
    logging.info('Client connected to voice channel on guild: %s', guild_id)

async def _search(lavalink: lavalink.Client, query: str = None, search_prefix: str = None) -> lavalink.LoadResult:
    
    query = query.strip('<>')
    if search_prefix and not URL_RX.match(query):
        query = f'{search_prefix}:{query}'

    result = await lavalink.get_tracks(query=query)
    if result.load_type == LoadType.PLAYLIST and result.tracks:
        result.tracks[0].extra['playlist_url'] = query

    return result
        

async def _play(bot, result: lavalink.LoadResult, guild_id: int, author_id: int,
        text_id: int = 0, options: dict = None) -> hikari.Embed:
    
    if not result or result.load_type in (LoadType.NO_MATCHES, LoadType.LOAD_FAILED):
        logging.warning('Failed to load search result')
        return

    player = bot.d.lavalink.player_manager.get(guild_id)
    if not player or not player.is_connected:
        await _join(bot, guild_id, author_id)
        player = bot.d.lavalink.player_manager.get(guild_id)

    index = 0 if options.get('next', '') == 'True' else -1
    loop = (options.get('loop', '') == 'True')
    shuffle = (options.get('shuffle', '') == 'True')

    result_type, description, image_url, num_tracks = None, None, None, 0
    if result.load_type in [LoadType.TRACK, LoadType.SEARCH]:
        result_type, num_tracks = 'track', 1
        track = result.tracks[0]
        track.extra['requester'] = author_id
        player.add(requester=author_id, track=track, index=index)
        player.set_loop(1) if loop else None
        image_url = track.artwork_url
        if track.source_name == 'spotify':
            description  = '[{0} - {1}]({2}) `{3}`\n Requested - <@{4}>\n'.format(
                track.title, track.author, track.uri, format_time(track.duration), track.requester)
        else:
            description = '[{0}]({1}) `{2}`\nRequested - <@{3}>'.format(
                track.title, track.uri, format_time(track.duration), author_id)

    if result.load_type == LoadType.PLAYLIST:
        result_type = 'playlist'
        tracks = result.tracks
        num_tracks = len(tracks)
        if not result.plugin_info or result.plugin_info.get('type') not in ('artist', 'playlist', 'album'):
            playlist_url = tracks[0].extra.get('playlist_url', None)    # get url from query
            description = 'Playlist [{0}]({1}) - {2} tracks added to queue <@{3}>'.format(
                result.playlist_info.name, playlist_url, num_tracks, author_id)
        else:
            plugin_info = result.plugin_info
            result_type = plugin_info.get('type')
            if result_type == 'artist':
                playlist_url, image_url,  = plugin_info.get('url'), plugin_info.get('artworkUrl')
                description = '[{0}]({1}) - `{2} tracks`\nRequested - <@{3}>'.format(
                    plugin_info.get('author').upper(), playlist_url, num_tracks, author_id)
            elif result_type == 'playlist':
                playlist_url, image_url,  = plugin_info.get('url'), plugin_info.get('artworkUrl')
                description = '[{0}]({1}) `{2} track(s)`\nRequested - <@{3}>'.format(
                    result.playlist_info.name, playlist_url, num_tracks, author_id)
            elif result_type == 'album':
                playlist_url, image_url,  = plugin_info.get('url'), plugin_info.get('artworkUrl')
                description = '[{0} - {1}]({2}) `{3} track(s)`\nRequested - <@{4}>'.format(
                    result.playlist_info.name, plugin_info.get('author'), playlist_url, num_tracks, author_id)
            else:
                raise BaseException('Unknown result type!')
        while tracks:
            pop_at = randrange(len(tracks)) if shuffle else 0
            track = tracks.pop(pop_at)
            track.extra['requester'] = author_id
            player.add(requester=author_id, track=track)
        player.set_loop(2) if loop else None

    bot.d.guilds[guild_id].channel_id = text_id
    if not player.is_playing:
        await player.play()

    return hikari.Embed(
        title=f'{result_type.capitalize()} added',
        description=description,
        color=COLOR_DICT['GREEN'],
    ).set_thumbnail(image_url)