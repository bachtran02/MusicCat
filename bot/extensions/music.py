import os
import re
import random
import logging
import hikari
import lavalink
import lightbulb
from requests import HTTPError
from googleapiclient.discovery import build

# from bot.library.StreamCount import StreamCount
from bot.library.autoqueue import Autoqueue
from bot.library.player import CustomPlayer
from bot.logger.custom_logger import track_logger
from bot.impl import _join, _play
from bot.spotify import Spotify
from bot.checks import valid_user_voice, player_playing, player_connected
from bot.constants import COLOR_DICT, BASE_YT_URL
from bot.utils import duration_str, player_bar
from bot.components import generate_rows, handle_responses

plugin = lightbulb.Plugin('Music', 'Music commands')

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

        try:
            await plugin.bot.rest.create_message(
                channel=player.textchannel_id,
                embed=hikari.Embed(
                    description = f'▶️ **Now playing:** [{track.title}]({track.uri}) - <@{track.requester}>',
                    colour = COLOR_DICT['GREEN']
                ))
        except Exception as error:
            pass

        # add to autoqueue
        if player.is_autoplay:
            related_tracks = await plugin.bot.d.autoqueue.get_related(track.identifier)
            player.add_autoplay(related_tracks)

        # plugin.bot.d.StreamCount.handle_stream(track)
        track_logger.info('%s - %s - %s', track.title, track.author, track.uri)
        logging.info('Track started on guild: %s', event.player.guild_id)

    @lavalink.listener(lavalink.TrackEndEvent)
    async def track_end(self, event: lavalink.TrackEndEvent):
        
        # player = plugin.bot.d.lavalink.player_manager.get(event.player.guild_id)
        logging.info('Track finished on guild: %s', event.player.guild_id)

    @lavalink.listener(lavalink.QueueEndEvent)
    async def queue_finish(self, event: lavalink.QueueEndEvent):

        player = plugin.bot.d.lavalink.player_manager.get(event.player.guild_id)
        if player.is_autoplay:
            await player.autoplay(plugin.bot.get_me().id)
        else:
            await plugin.bot.update_presence(activity=None)
        logging.info('Queue finished on guild: %s', event.player.guild_id)
        
    @lavalink.listener(lavalink.TrackExceptionEvent)
    async def track_exception(self, event: lavalink.TrackExceptionEvent):
        logging.warning('Track exception event happened on guild: %s', event.player.guild_id)


# on ready, connect to lavalink server
@plugin.listener(hikari.ShardReadyEvent)
async def start_bot(event: hikari.ShardReadyEvent) -> None:

    client = lavalink.Client(user_id=plugin.bot.get_me().id, player=CustomPlayer)
    client.add_event_hooks(EventHandler())

    client.add_node(
        host='lavalink',
        port=int(os.environ['LAVALINK_PORT']), password=os.environ['LAVALINK_PASS'],
        region='us', name='default-node', reconnect_attempts=-1
    )

    plugin.bot.d.lavalink = client
    plugin.bot.d.autoqueue = Autoqueue(client)
    # plugin.bot.d.StreamCount = StreamCount()
    plugin.bot.d.yt = client = build('youtube', 'v3', static_discovery=False, developerKey=os.environ['YOUTUBE_API_KEY'])
    
    try:
        plugin.bot.d.spotify = Spotify(os.environ['SPOTIFY_CLIENT_ID'], os.environ['SPOTIFY_CLIENT_SECRET'])
    except (KeyError | HTTPError) as error:
        logging.warning('Failed to build Spotify client - "%s"', error)
    


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('query', 'The query to search for.', modifier=lightbulb.OptionModifier.CONSUME_REST, required=True)
@lightbulb.option('next', 'Play the this track next', choices=['True'], required=False, default=False)
@lightbulb.option('loop', 'Loops track', choices=['True'], required=False, default=False)
@lightbulb.option('autoplay', 'Autoplay related track after queue ends', choices=['True', 'False'], required=False, default=None)
@lightbulb.command('play', 'Searches the query on youtube, or adds the URL to the queue.', auto_defer = True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def play(ctx: lightbulb.Context) -> None:
    """Searches the query on youtube, or adds the URL to the queue."""

    query = ctx.options.query

    embed = await _play(
        bot=plugin.bot, guild_id=ctx.guild_id, author_id=ctx.author.id,
        query=query, textchannel=ctx.channel_id, loop=(ctx.options.loop == 'True'),
        autoplay=ctx.options.autoplay,
    )
    if not embed:
        await ctx.respond('⚠️ No result for query!')
    else:
        await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_connected,
)
@lightbulb.command('leave', 'Leaves the voice channel the bot is in, clearing the queue.', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def leave(ctx: lightbulb.Context) -> None:
    """Leaves the voice channel the bot is in, clearing the queue."""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    await player.leave()
    await plugin.bot.update_presence(activity=None) # clear presence
    await plugin.bot.update_voice_state(ctx.guild_id, None) # disconnect from voice channel
    await ctx.respond('Left voice channel!')
    logging.info('Client disconnected from voice on guild: %s', ctx.guild_id)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command('join', 'Joins the voice channel you are in.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def join(ctx: lightbulb.Context) -> None:
    """Joins voice channel user is in"""
    
    try:
        channel_id = await _join(plugin.bot, ctx.guild_id, ctx.author.id)
    except TimeoutError as error:
        await ctx.respond(f'⚠️ {error}')
    else:
        await ctx.respond(f'Joined <#{channel_id}>')


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.command('stop', 'Stops the current song and clears queue.', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
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
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
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
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
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
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
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
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def seek(ctx : lightbulb.Context) -> None:
    """Seeks to a position of a track"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if not player.current.is_seekable:
        await ctx.respond('⚠️ Current track is not seekable!')
        return

    pos = ctx.options.position
    pos_rx = re.compile(r'\d+:\d{2}$')
    if not pos_rx.match(pos) or int(pos.split(':')[1]) >= 60:
        await ctx.respond('⚠️ Invalid position!')
        return
    
    minute, second = [int(x) for x in pos.split(':')]
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
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
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
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def queue(ctx : lightbulb.Context) -> None:
    """Current queue"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    
    autoplay_str = 'enabled' if player.is_autoplay else 'disabled'
    queue_description = f'**Current:** [{player.current.title}]({player.current.uri}) - <@!{player.current.requester}>' +'\n'
    queue_description += player_bar(player) 

    for i in range(min(len(player.queue), 10)):
        if i == 0:
            queue_description += '\n\n' + '**Up next:**'
        track = player.queue[i]
        queue_description = queue_description + '\n' + f'[{i + 1}. {track.title}]({track.uri}) `{duration_str(track.duration)}` <@!{track.requester}>'

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
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
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
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
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
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def autoplay(ctx:lightbulb.Context) -> None:
    """Enable/disable autoplay"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    
    if player.is_autoplay:
        player.is_autoplay = False
        player.autoqueue.clear()
    else:
        player.is_autoplay = True
        related_tracks = await plugin.bot.d.autoqueue.get_related(player.current.identifier)
        player.add_autoplay(related_tracks)

    await ctx.respond(embed=hikari.Embed(
            description = f'🎲 {("Autoplay enabled" if player.is_autoplay else "Autoplay disabled")}',
            colour = COLOR_DICT['BLUE']
        ))


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('latest', 'Play newest video in playlist', choices=['True'], default=None, required=False)
@lightbulb.command('chill', 'Play random linhnhichill', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def chill(ctx: lightbulb.Context) -> None:

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if not player or not player.is_connected:
        player = await _join(plugin.bot, ctx.guild_id, ctx.author.id)

    if ctx.options.latest:
        search = plugin.bot.d.yt.search().list(
            part='snippet',
            type='video',
            channelId='UCOGDtlp0av6Cp366BGS_PLQ',
            order='date',
            maxResults=10,
        ).execute()

        if not (isinstance(search, dict) or search.get('items', None)):
            await ctx.respond('⚠️ Failed to search for latest tracks')
            return
        
        yid = search['items'][random.randrange(len(search['items']))]['id']['videoId']
        results = await player.node.get_tracks(f'{BASE_YT_URL}/watch?v={yid}')

        if not results.load_type == 'TRACK_LOADED':
            await ctx.respond('⚠️ Failed to load track')
            return
        track = results.tracks[0]
    else:
        query = f'{BASE_YT_URL}/playlist?list=PL-F2EKRbzrNQte4aGjHp9cQau9peyPMw0'
        results = await player.node.get_tracks(query)

        if not results.load_type == 'PLAYLIST_LOADED':
            await ctx.respond('⚠️ Failed to load track!')
            return
        track = results.tracks[random.randrange(len(results.tracks))]
    
    player.add(track=track, requester=ctx.author.id)
    if not player.is_playing:
        await player.play()
    
    await ctx.respond(embed=hikari.Embed(
        description=f'[{track.title}]({track.uri}) added to queue <@{ctx.author.id}>',
        color=COLOR_DICT['GREEN']
    ))


# @plugin.command()
# @lightbulb.add_checks(lightbulb.guild_only)
# @lightbulb.command('top', 'Get tracks with most streams', auto_defer=True)
# @lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
# async def toptracks(ctx : lightbulb.Context) -> None:

#     embed = hikari.Embed(
#         title='Most Streamed Tracks',
#         description='',
#         color=COLOR_DICT['GREEN']
#     )

#     top_tracks = plugin.bot.d.StreamCount.get_top_tracks(10)
#     for i, track in enumerate(top_tracks):
#         embed.description += f'[{i + 1}. {track["title"]}]({track["url"]}) ({track["count"]})' + '\n'
#     if not embed.description:
#         embed.description = 'No data found!'

#     await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
)
@lightbulb.command('player', 'interactive guild music player', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def player(ctx: lightbulb.Context) -> None:
    """Interactive guild music player"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if not player or not player.is_playing:
        await ctx.respond('⚠️ Player is not playing!')
        return

    body = f'**Streaming:** [{player.current.title}]({player.current.uri})' +'\n'
    body += player_bar(player)
    body += f'Requested - <@!{player.current.requester}>'

    # Generate the action rows.
    rows = await generate_rows(ctx.bot)

    embed = hikari.Embed(
        description=body,
        color=COLOR_DICT['GREEN']
    )

    response = await ctx.respond(embed=embed, components=rows)
    message = await response.message()

    # Handle interaction responses to the initial message.
    await handle_responses(ctx.bot, ctx.author, message)


@plugin.listener(hikari.VoiceServerUpdateEvent)
async def voice_server_update(event: hikari.VoiceServerUpdateEvent) -> None:

    lavalink_data = {
        't': 'VOICE_SERVER_UPDATE',
        'd': {
            'guild_id': event.guild_id,
            'endpoint': event.endpoint[6:],  # get rid of wss://
            'token': event.token,
        }
    }
    await plugin.bot.d.lavalink.voice_update_handler(lavalink_data)

@plugin.listener(hikari.VoiceStateUpdateEvent)
async def voice_state_update(event: hikari.VoiceStateUpdateEvent) -> None:

    prev_state = event.old_state
    cur_state = event.state

    # send event update to lavalink server
    lavalink_data = {
        't': 'VOICE_STATE_UPDATE',
        'd': {
            'guild_id': cur_state.guild_id,
            'user_id': cur_state.user_id,
            'channel_id': cur_state.channel_id,
            'session_id': cur_state.session_id,
        }
    }
    await plugin.bot.d.lavalink.voice_update_handler(lavalink_data)

    bot_id = plugin.bot.get_me().id
    bot_voice_state = plugin.bot.cache.get_voice_state(cur_state.guild_id, bot_id)
    player = plugin.bot.d.lavalink.player_manager.get(cur_state.guild_id)

    if not bot_voice_state or cur_state.user_id == bot_id: # bot is disconnected by user or leave on command
        if not bot_voice_state and cur_state.user_id == bot_id :
            await player.leave()
            await plugin.bot.update_presence(activity=None) # clear presence
            await plugin.bot.update_voice_state(cur_state.guild_id, None) # disconnect from voice channel
            logging.info('Client disconnected from voice on guild: %s', cur_state.guild_id)    
        return
    
    # event occurs in channel not same as bot
    if not ((prev_state and prev_state.channel_id == bot_voice_state.channel_id) or
        (cur_state and cur_state.channel_id == bot_voice_state.channel_id)):
            return

    # player = plugin.bot.d.lavalink.player_manager.get(cur_state.guild_id)
    states = plugin.bot.cache.get_voice_states_view_for_guild(cur_state.guild_id).items()
    
    # count users in channel with bot
    cnt_user = len([state[0] for state in filter(lambda i: i[1].channel_id == bot_voice_state.channel_id, states)])

    if cnt_user == 1:  # only bot left in voice
        await player.leave()
        await plugin.bot.update_presence(activity=None) # clear presence
        await plugin.bot.update_voice_state(cur_state.guild_id, None) # disconnect from voice channel
        logging.info('Client disconnected from voice on guild: %s', cur_state.guild_id)    
        return

    if cnt_user > 2:  # not just bot & lone user -> resume player
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


@plugin.set_error_handler
async def foo_error_handler(event: lightbulb.CommandErrorEvent) -> bool:

    exception = event.exception
    if isinstance(exception, lightbulb.OnlyInGuild):
        await event.context.respond('⚠️ Cannot invoke Guild only command in DMs')
    if isinstance(exception, lightbulb.CheckFailure):
        await event.context.respond(f'⚠️ {exception}')


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
