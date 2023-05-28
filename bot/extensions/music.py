import os
import re
import random
import logging

import lavalink
import hikari
import lightbulb
import miru

from bot.library.player import CustomPlayer
from bot.logger.custom_logger import track_logger
from bot.impl import _join, _play, _search
from bot.checks import valid_user_voice, player_playing, player_connected
from bot.constants import COLOR_DICT
from bot.utils import format_time, player_bar
from bot.components import PlayerView, CustomTextSelect, RemoveButton

from bot.track_sources.spotify import SpofitySource
from bot.track_sources.custom_sources import lnchillSource

plugin = lightbulb.Plugin('Music', 'Basic music commands')

class EventHandler:
    """Events from the Lavalink server"""
    
    @lavalink.listener(lavalink.TrackStartEvent)
    async def track_start(self, event: lavalink.TrackStartEvent):

        player = plugin.bot.d.lavalink.player_manager.get(event.player.guild_id)
        track = player.current

        await plugin.bot.update_presence(
            activity = hikari.Activity(
                name=track.title,
                type=hikari.ActivityType.STREAMING,
                url=track.uri,
            ))
        
        # TODO: still create message on first play
        if player.loop == player.LOOP_SINGLE:  
            return

        description  = f'[{track.title}]({track.uri})'     + '\n'
        description += f'Requested - <@{track.requester}>' + '\n'
        try:
            await plugin.bot.rest.create_message(
                channel=player.textchannel_id,
                embed=hikari.Embed(
                    title='🎶 **Now playing**',
                    description = description,
                    colour = COLOR_DICT['GREEN'],
                    
                ).set_thumbnail(track.artwork_url)
            )
        except Exception as error:
            logging.error('Failed to send message on track start due to: %s', error)

        # add to autoqueue
        if player.is_autoplay:
            result = await plugin.bot.d.lavalink.get_tracks(query=f'getrec:{track.title}', check_local=True)
            player.add_autoqueue(result.tracks) if result.load_type == 'PLAYLIST_LOADED' else None

        track_logger.info('%s - %s - %s', track.title, track.author, track.uri)
        logging.info('Track started on guild: %s', event.player.guild_id)

    @lavalink.listener(lavalink.TrackEndEvent)
    async def track_end(self, event: lavalink.TrackEndEvent):
        logging.info('Track finished on guild: %s', event.player.guild_id)

    @lavalink.listener(lavalink.QueueEndEvent)
    async def queue_finish(self, event: lavalink.QueueEndEvent):

        player = plugin.bot.d.lavalink.player_manager.get(event.player.guild_id)
        if player.is_autoplay:
            await player.autoplay()
        else:
            await plugin.bot.update_presence(activity=None)
        logging.info('Queue finished on guild: %s', event.player.guild_id)
        
    @lavalink.listener(lavalink.TrackExceptionEvent)
    async def track_exception(self, event: lavalink.TrackExceptionEvent):
        logging.warning('Track exception event happened on guild: %s', event.player.guild_id)


# on ready, create a node to connect to lavalink server
@plugin.listener(hikari.ShardReadyEvent)
async def start_bot(event: hikari.ShardReadyEvent) -> None:

    client = lavalink.Client(user_id=plugin.bot.get_me().id, player=CustomPlayer)
    client.add_event_hooks(EventHandler())
    client.add_node(
        host='localhost',
        port=int(os.environ['LAVALINK_PORT']), password=os.environ['LAVALINK_PASS'],
        region='us', name='default-node'
    )
    client.register_source(
        SpofitySource(
            client_id=os.environ['SPOTIFY_CLIENT_ID'],
            client_secret=os.environ['SPOTIFY_CLIENT_SECRET']
        )
    )
    client.register_source(
        lnchillSource(token=os.environ['YOUTUBE_API_KEY'])
    )
    plugin.bot.d.lavalink = client
    

@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('query', 'The query to search for.', modifier=lightbulb.OptionModifier.CONSUME_REST, required=True)
@lightbulb.option('autoplay', 'Autoplay related track after queue ends', choices=['True', 'False'], required=False, default=None)
@lightbulb.option('loop', 'Loops track', choices=['True'], required=False, default=False)
@lightbulb.option('next', 'Play the this track next', choices=['True'], required=False, default=False)
@lightbulb.option('shuffle', 'Shuffle playlist', choices=['True'], required=False, default=False)
@lightbulb.command('play', 'Searches the query on youtube, or adds the URL to the queue.', auto_defer = True)
@lightbulb.implements(lightbulb.SlashCommand)
async def play(ctx: lightbulb.Context) -> None:
    """Searches the query on youtube, or adds the URL to the queue."""

    query = ctx.options.query
    index = 0 if ctx.options.next == 'True' else -1 
    autoplay = -1 if ctx.options.autoplay == 'False' else int(ctx.options.autoplay is not None)
    
    result = await _search(lavalink=plugin.bot.d.lavalink, query=query)
    embed = await _play(
        bot=plugin.bot, guild_id=ctx.guild_id, author_id=ctx.author.id,
        result=result, textchannel=ctx.channel_id, loop=(ctx.options.loop == 'True'),
        autoplay=autoplay, index=index, shuffle=(ctx.options.shuffle == 'True'),)
    if not embed:
        await ctx.respond('⚠️ No result for query!')
    else:
        await ctx.respond(embed=embed, delete_after=30)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_connected,
)
@lightbulb.command('leave', 'Leaves the voice channel the bot is in, clearing the queue.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def leave(ctx: lightbulb.Context) -> None:
    """Leaves the voice channel the bot is in, clearing the queue."""

    await plugin.bot.update_voice_state(ctx.guild_id, None) # disconnect from voice channel
    await ctx.respond(f'Left voice channel!')


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command('join', 'Joins the voice channel you are in.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def join(ctx: lightbulb.Context) -> None:
    """Joins voice channel user is in"""
   
    try:
        player = await _join(plugin.bot, ctx.guild_id, ctx.author.id)
    except RuntimeError as error:
        await ctx.respond(f'⚠️ {error}')
    else:
        await ctx.respond(f'Joined <#{player.channel_id}>')


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.command('stop', 'Stops the current song and clears queue.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def stop(ctx: lightbulb.Context) -> None:
    """Stops the current song (skip to continue)."""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    await player.stop()
    await plugin.bot.update_presence(activity=None) # clear presence

    await ctx.respond(embed=hikari.Embed(
        description = '⏹️ Stopped playing',
        colour = COLOR_DICT['RED']
    ))
    logging.info('Player stopped on guild: %s', ctx.guild_id)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.command('skip', 'Skips the current song.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def skip(ctx: lightbulb.Context) -> None:
    """Skips the current song."""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    cur_track = await player.skip()

    await ctx.respond(embed=hikari.Embed(
        description = f'Skipped: [{cur_track.title}]({cur_track.uri})',
        colour = COLOR_DICT['RED']
    ))
    logging.info('Track skipped on guild: %s', ctx.guild_id)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.command('pause', 'Pauses the current song.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def pause(ctx: lightbulb.Context) -> None:
    """Pauses the current song."""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    await player.set_pause(True)

    await ctx.respond(embed=hikari.Embed(
        description = '⏸️ Paused player',
        colour = COLOR_DICT['YELLOW']
    ))
    logging.info('Track paused on guild: %s', ctx.guild_id)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_connected,
)
@lightbulb.command('resume', 'Resumes playing the current song.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def resume(ctx: lightbulb.Context) -> None:
    """Resumes playing the current song."""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    await player.set_pause(False)

    await ctx.respond(embed=hikari.Embed(
        description = '▶️ Resumed player',
        colour = COLOR_DICT['GREEN']
    ))
    logging.info('Track resumed on guild: %s', ctx.guild_id)


# TODO: seek using H:M:S
@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.option('position', 'Position to seek (format: "[min]:[sec]" )', required=True)
@lightbulb.command('seek', "Seeks to a given position in the track", auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def seek(ctx : lightbulb.Context) -> None:
    """Seeks to a position of a track"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if not player.current.is_seekable:
        await ctx.respond('⚠️ Current track is not seekable!')
        return

    pos = ctx.options.position
    pos_rx = re.compile(r'\d+:\d{2}$')

    if not (pos_rx.match(pos) and int(pos.split(':')[1]) < 60):
        await ctx.respond('⚠️ Invalid position!')
        return
    
    [minute, second] = [int(x) for x in pos.split(':')]
    ms = minute * 60 * 1000 + second * 1000
    await player.seek(ms)

    await ctx.respond(embed=hikari.Embed(
        description = f'⏩ Player moved to `{minute}:{second:02}`',
        colour = COLOR_DICT['BLUE']
    ))


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.command('replay', 'Replay track', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def replay(ctx : lightbulb.Context) -> None:
    """Replay track from the start"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if not player.current.is_seekable:
        await ctx.respond('⚠️ Current track is not seekable!')
        return
    await player.seek(0)

    await ctx.respond(embed=hikari.Embed(
        description = f'⏩ Track replayed!',
        colour = COLOR_DICT['BLUE']
    ))

@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, player_playing,
)
@lightbulb.command('queue', 'Shows the next 10 songs in the queue', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def queue(ctx : lightbulb.Context) -> None:
    """Current queue"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    
    autoplay_str = 'enabled' if player.is_autoplay else 'disabled'
    queue_description = f'**Current:** [{player.current.title}]({player.current.uri}) - <@!{player.current.requester}>' +'\n'
    queue_description += player_bar(player) 

    for i in range(min(len(player.queue), 10)):
        if i == 0:
            queue_description += '\n' + '**Up next:**'
        track = player.queue[i]
        queue_description = queue_description + '\n' + f'{i + 1}. [{track.title}]({track.uri}) `{format_time(track.duration)}` <@!{track.requester}>'

    await ctx.respond(embed=hikari.Embed(
        title = f'🎵 Queue',
        description = queue_description,
        colour = COLOR_DICT['GREEN']
    ).set_footer(
        text=f'🎲 Autoplay: {autoplay_str}'
    ))


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.option('mode', 'Loop mode', choices=['track', 'queue', 'end'], required=False, default='track')
@lightbulb.command('loop', 'Loops current track or queue or ends loops', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def loop(ctx:lightbulb.Context) -> None:
    """Loop player by track or queue"""

    mode = ctx.options.mode
    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

    if mode == 'track':
        player.set_loop(1)
        body = '🔂 Enable Track loop!'
    elif mode == 'queue':
        player.set_loop(2)
        body = '🔁 Enable Queue loop!'
    else:
        player.set_loop(0)
        body = '⏭️ Disable loop!'
    
    await ctx.respond(embed=hikari.Embed(
        description = body,
        colour = COLOR_DICT['BLUE']
    ))


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.command('shuffle', 'Enable/disable shuffle', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def shuffle(ctx:lightbulb.Context) -> None:
    """Shuffle queue"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    player.set_shuffle(not player.shuffle)
   
    await ctx.respond(embed=hikari.Embed(
        description = f'🔀 {("Shuffle enabled" if player.shuffle else "Shuffle disabled")}',
        colour = COLOR_DICT['BLUE']
    ))


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.command('autoplay', 'Enable/disable autoplay', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def autoplay(ctx:lightbulb.Context) -> None:
    """Enable/disable autoplay"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

    if player.is_autoplay:
        player.is_autoplay = False
        player.autoqueue.clear()
    else:
        player.is_autoplay = True
        result = await plugin.bot.d.lavalink.get_tracks(query=f'getrec:{player.current.title}', check_local=True)
        player.add_autoqueue(result.tracks) if result.load_type == 'PLAYLIST_LOADED' else None

    await ctx.respond(embed=hikari.Embed(
        description = f'🎲 {("Autoplay enabled" if player.is_autoplay else "Autoplay disabled")}',
        colour = COLOR_DICT['BLUE']
    ))
    

@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('query', 'The query to search for.', modifier=lightbulb.OptionModifier.CONSUME_REST, required=True)
@lightbulb.command('search', 'Search & add specific YouTube track to queue', auto_defer = True)
@lightbulb.implements(lightbulb.SlashCommand)
async def search(ctx: lightbulb.Context) -> None:

    query = ctx.options.query

    result = await _search(lavalink=plugin.bot.d.lavalink, query=query)
    if result.load_type != 'SEARCH_RESULT':
        await ctx.respond('⚠️ Failed to load search result for query!', delete_after=30)
        return

    view = miru.View(timeout=60)
    options = [f'{i + 1}. {track.title[:55]}' for i, track in enumerate(result.tracks[:20])]
    options = [miru.SelectOption(label=option) for option in options]
    
    view.add_item(CustomTextSelect(options=options, placeholder='Select track to play'))
    view.add_item(RemoveButton(style=hikari.ButtonStyle.SECONDARY, emoji='❌'))

    message = await ctx.respond(
        components=view,
        delete_after=60,
        embed=hikari.Embed(
            color=COLOR_DICT['GREEN'],
            description=f'🔍 **Search results for:** `{query}`',
        ),)
    
    await view.start(message)
    await view.wait()  # Wait until the view is stopped or times out

    if not hasattr(view, 'choice'):  # remove btn is pressed or message timeout
        await message.delete()
        return
        
    result.load_type = lavalink.LoadType.TRACK
    result.tracks = [result.tracks[int(view.choice.split('.')[0]) - 1]]

    embed = await _play(
        bot=plugin.bot, result=result, guild_id=ctx.guild_id,
        author_id=ctx.author.id, textchannel=ctx.channel_id,
    )
    await message.edit(embed=embed, components=None)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing
)
@lightbulb.command('remove', 'Remove a track from queue', auto_defer = True)
@lightbulb.implements(lightbulb.SlashCommand)
async def remove(ctx: lightbulb.Context) -> None:

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if not player.queue:
        await ctx.respond('⚠️ Queue is emtpy!')
        return
    
    view = miru.View()
    options = [f'{i + 1}. {track.title[:55]}' for i, track in enumerate(player.queue[:20])]
    options = [miru.SelectOption(label=option) for option in options]
    
    view.add_item(CustomTextSelect(options=options, placeholder='Select track to remove'))
    view.add_item(RemoveButton(style=hikari.ButtonStyle.SECONDARY, emoji='❌'))

    message = await ctx.respond(components=view)
    await view.start(message)
    await view.wait()
    
    if not hasattr(view, 'choice'):  
        await message.delete()
        return
        
    popped_track = player.queue.pop(int(view.choice.split('.')[0]) - 1)
    await message.edit(
        components=None,
        embed=hikari.Embed(
            description = f'Removed: [{popped_track.title}]({popped_track.uri})',
            colour = COLOR_DICT['RED']
    ))


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
)
@lightbulb.command('player', 'interactive guild music player', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def player(ctx: lightbulb.Context) -> None:
    """Interactive guild music player"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if not player or not player.is_playing:
        await ctx.respond('⚠️ Player is not playing!')
        return

    desc = f'**Streaming:** [{player.current.title}]({player.current.uri})' +'\n'
    desc += player_bar(player)
    desc += f'Requested - <@!{player.current.requester}>'

    view = PlayerView()

    message = await ctx.respond(
        components=view,
        embed=hikari.Embed(
            description=desc,
            color=COLOR_DICT['GREEN']
        ).set_thumbnail(player.current.artwork_url)
    )

    await view.start(message)  # Start listening for interactions
    await view.wait()


@plugin.listener(hikari.VoiceServerUpdateEvent)
async def voice_server_update(event: hikari.VoiceServerUpdateEvent) -> None:

    await plugin.bot.d.lavalink.voice_update_handler({
        't': 'VOICE_SERVER_UPDATE',
        'd': {
            'guild_id': event.guild_id,
            'endpoint': event.endpoint[6:],  # get rid of wss://
            'token': event.token,
        }
    })

@plugin.listener(hikari.VoiceStateUpdateEvent)
async def voice_state_update(event: hikari.VoiceStateUpdateEvent) -> None:

    prev_state = event.old_state
    cur_state = event.state

    # send event update to lavalink server
    await plugin.bot.d.lavalink.voice_update_handler({
        't': 'VOICE_STATE_UPDATE',
        'd': {
            'guild_id': cur_state.guild_id,
            'user_id': cur_state.user_id,
            'channel_id': cur_state.channel_id,
            'session_id': cur_state.session_id,
        }
    })

    bot_id = plugin.bot.get_me().id
    bot_voice_state = plugin.bot.cache.get_voice_state(cur_state.guild_id, bot_id)
    player: CustomPlayer = plugin.bot.d.lavalink.player_manager.get(cur_state.guild_id)

    if not bot_voice_state or cur_state.user_id == bot_id:
        if not bot_voice_state and cur_state.user_id == bot_id:  # bot is disconnected
            player.clear_player()
            await plugin.bot.update_presence(activity=None) # clear presence
            logging.info('Client disconnected from voice on guild: %s', cur_state.guild_id)
        return
    
    # event occurs in channel not same as bot
    if not ((prev_state and prev_state.channel_id == bot_voice_state.channel_id) or
        (cur_state and cur_state.channel_id == bot_voice_state.channel_id)):
            return

    states = plugin.bot.cache.get_voice_states_view_for_guild(cur_state.guild_id).items()
    
    # count users in channel with bot
    cnt_user = len([state[0] for state in filter(lambda i: i[1].channel_id == bot_voice_state.channel_id, states)])

    if cnt_user == 1:  # only bot left in voice
        await plugin.bot.update_voice_state(cur_state.guild_id, None)
        return

    if cnt_user > 2:  # not just bot & lone user -> resume player (TODO: doesn't resume if bot is not autopaused)
        if player and player.paused:
            await player.set_pause(False)
        return
    
    # resume player when user undeafens
    if prev_state.is_self_deafened and not cur_state.is_self_deafened:
        if player and player.paused:
            await player.set_pause(False)
            logging.info('Track resumed on guild: %s', event.guild_id)
    
    # pause player when user deafens
    if not prev_state.is_self_deafened and cur_state.is_self_deafened:
        if not player or not player.is_playing:
            return
        await player.set_pause(True)
        logging.info('Track paused on guild: %s', event.guild_id)


# TODO: handle mutliple checks failed 
@plugin.set_error_handler
async def foo_error_handler(event: lightbulb.CommandErrorEvent) -> bool:

    exception = event.exception
    if isinstance(exception, lightbulb.OnlyInGuild):
        await event.context.respond('⚠️ Cannot invoke Guild only command in DMs')
    if isinstance(exception, lightbulb.CheckFailure):
        await event.context.respond(f'⚠️ {exception}')


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
