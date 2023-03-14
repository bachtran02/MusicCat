import os
import re
import random
import hikari
import logging
import lavalink
import lightbulb
from googleapiclient.discovery import build

from requests import HTTPError
from googleapiclient import errors

from bot.logger import track_logger
from bot.library.Spotify import Spotify
from bot.library.StreamCount import StreamCount
from bot.library.MusicCommand import MusicCommand, MusicCommandError

BASE_YT_URL = 'https://www.youtube.com/watch'

plugin = lightbulb.Plugin("Music", "🎧 Music commands")

class EventHandler:
    """Events from the Lavalink server"""
    
    @lavalink.listener(lavalink.TrackStartEvent)
    async def track_start(self, event: lavalink.TrackStartEvent):

        player = plugin.bot.d.lavalink.player_manager.get(event.player.guild_id)
        track = player.current
        
        await plugin.bot.update_presence(
            activity = hikari.Activity(
            name = f"{track.author} - {track.title}",
            type = hikari.ActivityType.LISTENING
        ))

        logging.info("Track started on guild: %s", event.player.guild_id)
        track_logger.info("%s - %s - %s", track.title, track.author, track.uri)

        player.store['last_played'] = track.identifier  
        plugin.bot.d.StreamCount.handle_stream(track)

    @lavalink.listener(lavalink.TrackEndEvent)
    async def track_end(self, event: lavalink.TrackEndEvent):

        player = plugin.bot.d.lavalink.player_manager.get(event.player.guild_id)

        if not player.queue:
            await plugin.bot.update_presence(
                activity = hikari.Activity(
                    name=f"/play",
                    type=hikari.ActivityType.LISTENING
                ))
            
        logging.info("Track finished on guild: %s", event.player.guild_id)

    @lavalink.listener(lavalink.TrackExceptionEvent)
    async def track_exception(self, event: lavalink.TrackExceptionEvent):
        logging.warning("Track exception event happened on guild: %d", event.player.guild_id)

    @lavalink.listener(lavalink.QueueEndEvent)
    async def queue_finish(self, event: lavalink.QueueEndEvent):
        
        player = plugin.bot.d.lavalink.player_manager.get(event.player.guild_id)

        # autoplay
        if not plugin.bot.d.youtube or player.store['autoplay'] is not True:
            return
        
        search = plugin.bot.d.youtube.search().list(
            part="snippet",
            type='video',
            relatedToVideoId=player.store['last_played'],
            maxResults=10
        ).execute()

        if not search['items']:
            return

        video_id = search['items'][random.randint(0, len(search['items']) - 1)]['id']['videoId']
        track_url = f"{BASE_YT_URL}?v={video_id}"

        try:
            e = await plugin.bot.d.music._play(
                guild_id=event.player.guild_id,
                author_id=player.store['requester'],
                channel_id =player.store['channel_id'],
                query=track_url,
                autoplay=True,
            )
        except MusicCommandError as e:
            await plugin.bot.rest.create_message(
                channel=player.store['channel_id'],
                content=e
            )
        else:
            await plugin.bot.rest.create_message(
                channel=player.store['channel_id'],
                embed=e
            )

# on ready, connect to lavalink server
@plugin.listener(hikari.ShardReadyEvent)
async def start_bot(event: hikari.ShardReadyEvent) -> None:

    client = lavalink.Client(plugin.bot.get_me().id)
    client.add_node(
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
        plugin.bot.d.youtube = build('youtube', 'v3', static_discovery=False, developerKey=os.environ["YOUTUBE_API_KEY"])
    except KeyError as e:
        logging.warning("Missing Key in .env file - %s", e)
    except errors.HttpError as e:
        logging.warning("Google API client error - '%s'", e.reason)

    try:
        plugin.bot.d.spotify = Spotify(os.environ['SPOTIFY_CLIENT_ID'], os.environ['SPOTIFY_CLIENT_SECRET'])
    except KeyError as e:
        logging.warning("Missing Key in .env file - %s", e)
    except HTTPError as e:
        logging.warning("Spotify API client error - '%s'", e)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option("query", "The query to search for.", modifier=lightbulb.OptionModifier.CONSUME_REST, required=True)
@lightbulb.option("loop", "Loops track", choices=['True'], required=False, default=False)
@lightbulb.option("autoplay", "Autoplay related track after queue ends", choices=['True'], required=False, default=False)
@lightbulb.command("play", "Searches the query on youtube, or adds the URL to the queue.", auto_defer = True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def play(ctx: lightbulb.Context) -> None:
    """Searches the query on youtube, or adds the URL to the queue."""

    query = ctx.options.query
    try:
        e = await plugin.bot.d.music._play(
            guild_id=ctx.guild_id,
            author_id=ctx.author.id,
            channel_id = ctx.channel_id,
            query=query,
            loop=(ctx.options.loop == 'True'),
            autoplay=(ctx.options.autoplay == 'True'),
        )
    except MusicCommandError as e:
        await ctx.respond(e)
    else:
        await ctx.respond(embed=e)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("leave", "Leaves the voice channel the bot is in, clearing the queue.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def leave(ctx: lightbulb.Context) -> None:
    """Leaves the voice channel the bot is in, clearing the queue."""

    try:
        await plugin.bot.d.music._leave(ctx.guild_id)
    except MusicCommandError as e:
        await ctx.respond(e)
    else:
        await ctx.respond("Left voice channel!")
        

@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("join", "Joins the voice channel you are in.", auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def join(ctx: lightbulb.Context) -> None:
    
    try:
        channel_id = await plugin.bot.d.music._join(ctx.guild_id, ctx.author.id)
    except MusicCommandError as e:
        await ctx.respond(e)
    else:
        await ctx.respond(f"Joined <#{channel_id}>")


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("stop", "Stops the current song and clears queue.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def stop(ctx: lightbulb.Context) -> None:
    """Stops the current song (skip to continue)."""

    try:
        e = await plugin.bot.d.music._stop(ctx.guild_id)
    except MusicCommandError as e:
        await ctx.respond(e)
    else:
        await ctx.respond(embed=e)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("skip", "Skips the current song.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def skip(ctx: lightbulb.Context) -> None:
    """Skips the current song."""

    try:
        e = await plugin.bot.d.music._skip(ctx.guild_id)
    except MusicCommandError as e:
        await ctx.respond(e)
    else:
        await ctx.respond(embed=e)

@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("pause", "Pauses the current song.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def pause(ctx: lightbulb.Context) -> None:
    """Pauses the current song."""

    try:
        e = await plugin.bot.d.music._pause(ctx.guild_id)
    except MusicCommandError as e:
        await ctx.respond(e)
    else:
        await ctx.respond(embed=e)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("resume", "Resumes playing the current song.", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def resume(ctx: lightbulb.Context) -> None:
    """Resumes playing the current song."""

    try:
        e = await plugin.bot.d.music._resume(ctx.guild_id)
    except MusicCommandError as e:
        await ctx.respond(e)
    else:
        await ctx.respond(embed=e)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option("position", "Position to seek (format: '[min]:[sec]' )", required=True)
@lightbulb.command("seek", "Seeks to a given position in the track", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def seek(ctx : lightbulb.Context) -> None:
    
    pos = ctx.options.position
    try:
        e = await plugin.bot.d.music._seek(ctx.guild_id, pos)
    except MusicCommandError as e:
        await ctx.respond(e)
    else:
        await ctx.respond(embed=e)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("restart", "Restart track", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def restart(ctx : lightbulb.Context) -> None:
    
    try:
        e = await plugin.bot.d.music._seek(ctx.guild_id, '0:00')
    except MusicCommandError as e:
        await ctx.respond(e)
    else:
        await ctx.respond(embed=e)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("queue", "Shows the next 10 songs in the queue", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def queue(ctx : lightbulb.Context) -> None:
    
    try:
        e = await plugin.bot.d.music._queue(ctx.guild_id)
    except MusicCommandError as e:
        await ctx.respond(e)
    else:
        await ctx.respond(embed=e)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option("mode", "Mode for loop", choices=['track', 'queue', 'end'], required=False, default='track')
@lightbulb.command("loop", "Loops current track or queue or ends loops", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def loop(ctx : lightbulb.Context) -> None:
    
    mode = ctx.options.mode
    try:
        e = await plugin.bot.d.music._loop(ctx.guild_id, mode)
    except MusicCommandError as e:
        await ctx.respond(e)
    else:
        await ctx.respond(embed=e)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("shuffle", "Enable/disable shuffle", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def shuffle(ctx : lightbulb.Context) -> None:
    
    try:
        e = await plugin.bot.d.music._shuffle(ctx.guild_id)
    except MusicCommandError as e:
        await ctx.respond(e)
    else:
        await ctx.respond(embed=e)

@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option("latest", "Play newest video in playlist", choices=['True'], default=None, required=False)
@lightbulb.command("chill", "Play random linhnhichill", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def chill(ctx: lightbulb.Context) -> None:

    if not plugin.bot.d.youtube:
        logging.warning("Failed to use '/chill'! Check YouTube API credentials")
        await ctx.respond(":warning: Failed to use command!")
        return
    
    vid_id = None
    rand_vid = -1
    next_page_token = None
    while True:
        res = plugin.bot.d.youtube.playlistItems().list(
            playlistId='PL-F2EKRbzrNS0mQqAW6tt75FTgf4j5gjS',  # linhnhichill's playlist ID
            part='snippet',
            pageToken = next_page_token,
            maxResults=50
        ).execute()

        next_page_token = res.get('nextPageToken')

        if not ctx.options.latest:
            if rand_vid == -1:
                rand_vid = random.randint(0, res['pageInfo']['totalResults'] - 1)
            if rand_vid < 50:
                vid_id = res['items'][rand_vid]['snippet']['resourceId']['videoId']  # id
                break
            rand_vid -= 50
        else:
            if not next_page_token:
                vid_id = res['items'][len(res)-1]['snippet']['resourceId']['videoId']  # id
                break

    assert vid_id is not None

    try:
        e = await plugin.bot.d.music._play(
            guild_id=ctx.guild_id, 
            author_id=ctx.author.id,
            channel_id=ctx.channel_id,
            query=f"{BASE_YT_URL}?v={vid_id}",
        )
    except MusicCommandError as e:
        await ctx.respond(e)
    else:
        await ctx.respond(embed=e)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("top", "Get tracks with most streams", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def topTracks(ctx : lightbulb.Context) -> None:
    
    e = hikari.Embed(
        title="Most Streamed Tracks",
        description="",
        color=0x76ffa1
    )

    top_tracks = plugin.bot.d.StreamCount.get_top_tracks()
    for i, track in enumerate(top_tracks):
        e.description += f"[{i + 1}. {track['title']}]({track['url']}) ({track['count']})" + '\n'
    if not e.description:
        e.description = "No data found!"

    await ctx.respond(embed=e)


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

    if not bot_voice_state or cur_state.user_id == bot_id:
        return

    states = plugin.bot.cache.get_voice_states_view_for_guild(cur_state.guild_id).items()
    
    player = plugin.bot.d.lavalink.player_manager.get(cur_state.guild_id)
    # count users in channel with bot
    cnt_user = len([state[0] for state in filter(lambda i: i[1].channel_id == bot_voice_state.channel_id, states)])

    if cnt_user == 1:  # only bot left in voice
        await plugin.bot.d.music._leave(cur_state.guild_id)
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
        logging.info("Track resumed on guild: %s", event.guild_id)
    
    # pause player when user deafens
    if not prev_state.is_self_deafened and cur_state.is_self_deafened:
        if not player or not player.is_playing:
            return
        
        await player.set_pause(True)
        logging.info("Track paused on guild: %s", event.guild_id)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
