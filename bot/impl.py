import re
import logging
from random import randrange

import hikari
import lavalink
from lavalink import LoadType

from bot.constants import COLOR_DICT

async def _join(bot, guild_id: int, author_id: int) -> lavalink.DefaultPlayer:
    
    assert guild_id is not None

    states = bot.cache.get_voice_states_view_for_guild(guild_id)
    voice_state = [state[1] for state in filter(lambda i : i[0] == author_id, states.items())]
    channel_id = voice_state[0].channel_id  # voice channel user is in

    player = bot.d.lavalink.player_manager.create(guild_id=guild_id)
    await bot.update_voice_state(guild_id, channel_id, self_deaf=True)  # can raise RuntimeError
    player.channel_id = channel_id  # TODO: improve this
    
    logging.info('Client connected to voice channel on guild: %s', guild_id)
    return player

async def _search(lavalink: lavalink.Client, source: str = None, client = None, query: str = None) -> lavalink.LoadResult:
    
    query = query.strip('<>')  # <url> to suppress embed on Discord

    if source:
        # if custom client is not given then use lavalink client
        client = lavalink if not client else None  
        if not (source := lavalink.get_source(source_name=source)):
            logging.error('Failed to retrieve custom source')
            raise BaseException('Source not found!')
        return await source.load_item(query=query, client=client, use_source=True)

    url_rx = re.compile(r'https?://(?:www\.)?.+')
    if not url_rx.match(query):
        query = f'ytsearch:{query}'  # or ytsearch:
    
    return await lavalink.get_tracks(query=query, check_local=True)

async def _play(bot, result: lavalink.LoadResult, guild_id: int, author_id: int,
        textchannel: int = 0, loop: bool = False, shuffle: bool = False, index: int = -1, 
        autoplay: int = 0) -> hikari.Embed:
    
    assert result is not None

    if result.load_type in [LoadType.NO_MATCHES, LoadType.LOAD_FAILED]:
        logging.warning('Failed to load search result for query due to %s', result.load_type)
        return None  # TODO: return error embed
    
    # get player or _join to get player
    player = bot.d.lavalink.player_manager.get(guild_id)
    if not player or not player.is_connected:
        await _join(bot, guild_id, author_id)
        player = bot.d.lavalink.player_manager.get(guild_id)

    description = None
    if result.load_type in [LoadType.TRACK, LoadType.SEARCH]:

        track = result.tracks[0]
        player.add(requester=author_id, track=track, index=index)
        player.set_loop(1) if loop else None
        description = f'[{track.title}]({track.uri}) added to queue <@{author_id}>'

    if result.load_type == LoadType.PLAYLIST:
        
        query = 'https://www.youtube.com/watch?v=X7sSE3yCNLI'  # temporary for error

        tracks = result.tracks
        while result.tracks:
            pop_at = randrange(len(tracks)) if shuffle else 0
            player.add(requester=author_id, track=tracks.pop(pop_at))

        player.set_loop(2) if loop else None
        description = f'Playlist [{result.playlist_info.name}]({query})' \
            f' - {len(result["tracks"])} tracks added to queue <@{author_id}>'

    player.textchannel_id = textchannel
    if autoplay:
        if autoplay == 1:
            player.is_autoplay = True
        elif autoplay == -1:
            player.is_autoplay = False
    
    if not player.is_playing:
        await player.play()

    return hikari.Embed(
        description=description,
        color=COLOR_DICT['GREEN']
    )