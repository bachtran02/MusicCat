import os
import random
import logging
import hikari
import lavalink
import lightbulb

from googleapiclient import errors
from googleapiclient.discovery import build
from requests import HTTPError

from bot.logger.custom_logger import track_logger
from bot.library.Spotify import Spotify
from bot.library.StreamCount import StreamCount
from bot.library.MusicCommand import MusicCommand, MusicCommandError
from bot.library.CustomChecks import valid_user_voice, player_playing, player_connected
from bot.constants import COLOR_DICT, BASE_YT_URL, PLAYER_STORE_INIT

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
            ),)
        player.store['last_played'] = track  # lavalink.AudioTrack
        plugin.bot.d.StreamCount.handle_stream(track)

        track_logger.info('%s - %s - %s', track.title, track.author, track.uri)
        logging.info('Track started on guild: %s', event.player.guild_id)

    @lavalink.listener(lavalink.TrackEndEvent)
    async def track_end(self, event: lavalink.TrackEndEvent):
        
        player = plugin.bot.d.lavalink.player_manager.get(event.player.guild_id)
        logging.info('Track finished on guild: %s', event.player.guild_id)

    @lavalink.listener(lavalink.QueueEndEvent)
    async def queue_finish(self, event: lavalink.QueueEndEvent):

        player = plugin.bot.d.lavalink.player_manager.get(event.player.guild_id)
        if not (plugin.bot.d.youtube and player.store['autoplay']):
            await plugin.bot.update_presence(activity=None)
            return
        try:
            [embed, channel_id] = await plugin.bot.d.music.autoplay(event.player.guild_id)
        except MusicCommandError as error:
            await plugin.bot.rest.create_message(
                channel=channel_id,
                content=error
            )
        else:
            if embed:
                await plugin.bot.rest.create_message(
                    channel=channel_id,
                    embed=embed
                )
        logging.info('Queue finished on guild: %s', event.player.guild_id)
        
    @lavalink.listener(lavalink.TrackExceptionEvent)
    async def track_exception(self, event: lavalink.TrackExceptionEvent):
        logging.warning('Track exception event happened on guild: %s', event.player.guild_id)


# on ready, connect to lavalink server
@plugin.listener(hikari.ShardReadyEvent)
async def start_bot(event: hikari.ShardReadyEvent) -> None:

    client = lavalink.Client(plugin.bot.get_me().id)
    client.add_node(
        # host='lavalink',
        host='localhost',
        port=int(os.environ['LAVALINK_PORT']),
        password=os.environ['LAVALINK_PASS'],
        region='us',
        name='default-node'
    )
    client.add_event_hooks(EventHandler())

    plugin.bot.d.lavalink = client
    plugin.bot.d.music = MusicCommand(plugin.bot)
    plugin.bot.d.StreamCount = StreamCount()
    
    try:
        plugin.bot.d.youtube = build('youtube', 'v3', static_discovery=False, developerKey=os.environ['YOUTUBE_API_KEY'])
    except (KeyError | errors.HTTPError) as error:
        logging.warning('Failed to build YouTube client - "%s"', error)
    try:
        plugin.bot.d.spotify = Spotify(os.environ['SPOTIFY_CLIENT_ID'], os.environ['SPOTIFY_CLIENT_SECRET'])
    except (KeyError | errors.HTTPError) as error:
        logging.warning('Failed to build Spotify client - "%s"', error)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
    valid_user_voice,
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
    try:
        embed = await plugin.bot.d.music.play(
            guild_id=ctx.guild_id,
            author_id=ctx.author.id,
            channel_id = ctx.channel_id,
            query=query,
            index=0 if ctx.options.next else None,
            loop=(ctx.options.loop == 'True'),
            autoplay=ctx.options.autoplay,
        )
    except MusicCommandError as error:
        await ctx.respond(f'⚠️ {error}')
    else:
        await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
    valid_user_voice,
    player_connected,
)
@lightbulb.command('leave', 'Leaves the voice channel the bot is in, clearing the queue.', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def leave(ctx: lightbulb.Context) -> None:
    """Leaves the voice channel the bot is in, clearing the queue."""

    await plugin.bot.d.music.leave(ctx.guild_id)
    await ctx.respond('Left voice channel!') 


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command('join', 'Joins the voice channel you are in.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def join(ctx: lightbulb.Context) -> None:
    """Joins voice channel user is in"""
    
    try:
        channel_id = await plugin.bot.d.music.join(ctx.guild_id, ctx.author.id)
    except TimeoutError as error:
        await ctx.respond(f'⚠️ {error}')
    else:
        await ctx.respond(f'Joined <#{channel_id}>')


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
    valid_user_voice,
    player_playing,
)
@lightbulb.command('stop', 'Stops the current song and clears queue.', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def stop(ctx: lightbulb.Context) -> None:
    """Stops the current song (skip to continue)."""

    embed = await plugin.bot.d.music.stop(ctx.guild_id)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
    valid_user_voice,
    player_playing,
)
@lightbulb.command('skip', 'Skips the current song.', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def skip(ctx: lightbulb.Context) -> None:
    """Skips the current song."""

    embed = await plugin.bot.d.music.skip(ctx.guild_id)
    await ctx.respond(embed=embed)

@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
    valid_user_voice,
    player_playing,
)
@lightbulb.command('pause', 'Pauses the current song.', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def pause(ctx: lightbulb.Context) -> None:
    """Pauses the current song."""

    embed = await plugin.bot.d.music.pause(ctx.guild_id)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
    valid_user_voice,
    player_connected,
)
@lightbulb.command('resume', 'Resumes playing the current song.', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def resume(ctx: lightbulb.Context) -> None:
    """Resumes playing the current song."""

    embed = await plugin.bot.d.music.resume(ctx.guild_id)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
    valid_user_voice,
    player_playing,
)
@lightbulb.option('position', 'Position to seek (format: "[min]:[sec]" )', required=True)
@lightbulb.command('seek', "Seeks to a given position in the track", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def seek(ctx : lightbulb.Context) -> None:
    """Seeks to a position of a track"""

    pos = ctx.options.position
    try:
        embed = await plugin.bot.d.music.seek(ctx.guild_id, pos)
    except MusicCommandError as error:
        await ctx.respond(f'⚠️ {error}')
    else:
        await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
    valid_user_voice,
    player_playing,
)
@lightbulb.command('replay', 'Replay track', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def restart(ctx : lightbulb.Context) -> None:
    """Replay track from the start"""

    embed = await plugin.bot.d.music.seek(ctx.guild_id, '0:00')
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
    player_playing,
)
@lightbulb.command('queue', 'Shows the next 10 songs in the queue', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def queue(ctx : lightbulb.Context) -> None:
    
    e = await plugin.bot.d.music.queue(ctx.guild_id)
    await ctx.respond(embed=e)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
    valid_user_voice,
    player_playing,
)
@lightbulb.option('mode', 'Loop mode', choices=['track', 'queue', 'end'], required=False, default='track')
@lightbulb.command('loop', 'Loops current track or queue or ends loops', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def loop(ctx:lightbulb.Context) -> None:
    """Loop player by track or queue"""

    mode = ctx.options.mode
    embed = await plugin.bot.d.music.loop(ctx.guild_id, mode)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
    valid_user_voice,
    player_playing,
)
@lightbulb.command('shuffle', 'Enable/disable shuffle', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def shuffle(ctx:lightbulb.Context) -> None:
    """Shuffle queue"""

    embed = await plugin.bot.d.music.shuffle(ctx.guild_id)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
    valid_user_voice,
    player_playing,
)
@lightbulb.command('autoplay', 'Enable/disable autoplay', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def flip_autoplay(ctx:lightbulb.Context) -> None:
    """Autoplay after queue finishes"""

    embed = await plugin.bot.d.music.flip_autoplay(ctx.guild_id, ctx.channel_id)
    await ctx.respond(embed=embed)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
    valid_user_voice,
)
@lightbulb.option('latest', 'Play newest video in playlist', choices=['True'], default=None, required=False)
@lightbulb.command('chill', 'Play random linhnhichill', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def chill(ctx: lightbulb.Context) -> None:

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if not player or not player.is_connected:
        await plugin.bot.d.music.join(ctx.guild_id, ctx.author.id)
        player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

    query = f'{BASE_YT_URL}/playlist?list=PL-F2EKRbzrNS0mQqAW6tt75FTgf4j5gjS'
    results = await player.node.get_tracks(query)

    if not results.load_type == 'PLAYLIST_LOADED':
        await ctx.respond('⚠️ Failed to load track!')

    track = results.tracks[random.randrange(len(results.tracks))]
    player.add(track=track, requester=ctx.author.id)
    if not player.is_playing:
        await player.play()
    
    await ctx.respond(
        embed=hikari.Embed(
            description=f'[{track.title}]({track.uri}) added to queue <@{ctx.author.id}>',
            color=COLOR_DICT['GREEN']
    ))


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command('top', 'Get tracks with most streams', auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def toptracks(ctx : lightbulb.Context) -> None:

    embed = hikari.Embed(
        title='Most Streamed Tracks',
        description='',
        color=COLOR_DICT['GREEN']
    )

    top_tracks = plugin.bot.d.StreamCount.get_top_tracks(10)
    for i, track in enumerate(top_tracks):
        embed.description += f'[{i + 1}. {track["title"]}]({track["url"]}) ({track["count"]})' + '\n'
    if not embed.description:
        embed.description = 'No data found!'

    await ctx.respond(embed=embed)


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

    if not bot_voice_state or cur_state.user_id == bot_id: # bot is disconnected by user or leave on command
        if not bot_voice_state and cur_state.user_id == bot_id :  
            await plugin.bot.d.music.leave(cur_state.guild_id)
        return
    
    # event occurs in channel not same as bot
    if not ((prev_state and prev_state.channel_id == bot_voice_state.channel_id) or
        (cur_state and cur_state.channel_id == bot_voice_state.channel_id)):
            return

    player = plugin.bot.d.lavalink.player_manager.get(cur_state.guild_id)
    states = plugin.bot.cache.get_voice_states_view_for_guild(cur_state.guild_id).items()
    
    # count users in channel with bot
    cnt_user = len([state[0] for state in filter(lambda i: i[1].channel_id == bot_voice_state.channel_id, states)])

    if cnt_user == 1:  # only bot left in voice
        await plugin.bot.d.music.leave(cur_state.guild_id)
        return
    if cnt_user > 2:  # not just bot & lone user -> resume player
        if player and player.paused:
            await player.set_pause(False)
        return
    
    # resume player when user undeafens
    if prev_state.is_self_deafened and not cur_state.is_self_deafened:
        if player and player.paused:
            await player.set_pause(False)
        else:
            return
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
