import os
import re
import random
import hikari
import logging
import lavalink
import lightbulb
from typing import Optional
from googleapiclient.discovery import build

from ashema.library.SpotifyClient import SpotifyClient

plugin = lightbulb.Plugin("Music", "🎧 Music commands")

url_rx = re.compile(r'https?://(?:www\.)?.+')

class EventHandler:
    """Events from the Lavalink server"""
    
    @lavalink.listener(lavalink.TrackStartEvent)
    async def track_start(self, event: lavalink.TrackStartEvent):
        logging.info("Track started on guild: %s", event.player.guild_id)

    @lavalink.listener(lavalink.TrackEndEvent)
    async def track_end(self, event: lavalink.TrackEndEvent):
        logging.info("Track finished on guild: %s", event.player.guild_id)

    @lavalink.listener(lavalink.TrackExceptionEvent)
    async def track_exception(self, event: lavalink.TrackExceptionEvent):
        logging.warning("Track exception event happened on guild: %d", event.player.guild_id)

    @lavalink.listener(lavalink.QueueEndEvent)
    async def queue_finish(self, event: lavalink.QueueEndEvent):
        pass

# on ready, connect to lavalink server
@plugin.listener(hikari.ShardReadyEvent)
async def start_lavalink(event: hikari.ShardReadyEvent) -> None:

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

    youtube = build('youtube', 'v3', static_discovery=False, developerKey=os.environ["YOUTUBE_API_KEY"])
    plugin.bot.d.youtube = youtube
    plugin.bot.d.spotify = SpotifyClient()


async def _join(ctx: lightbulb.Context) -> Optional[hikari.Snowflake]:
    assert ctx.guild_id is not None

    states = plugin.bot.cache.get_voice_states_view_for_guild(ctx.guild_id)

    voice_state = [state[1] for state in filter(lambda i : i[0] == ctx.author.id, states.items())]
    bot_voice_state = [state[1] for state in filter(lambda i: i[0] == ctx.bot.get_me().id, states.items())]

    if not voice_state:
        await ctx.respond(":warning: Connect to a voice channel first!")
        return None

    channel_id = voice_state[0].channel_id

    if bot_voice_state:
        if channel_id != bot_voice_state[0].channel_id:
            await ctx.respond(":warning: I am already playing in another Voice Channel!")
            return None

    try:
        await plugin.bot.update_voice_state(ctx.guild_id, channel_id, self_deaf=True)
        plugin.bot.d.lavalink.player_manager.create(guild_id=ctx.guild_id)  
    except TimeoutError:
        await ctx.respond(":warning: I was unable to connect to the voice channel, maybe missing permissions? or some internal issue.")
        return None
    
    logging.info("Client connected to voice channel on guild: %s", ctx.guild_id)
    return channel_id

async def _play(ctx: lightbulb.Context, query: str):
    assert ctx.guild_id is not None 

    query = query.strip('<>')
    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

    if not player or not player.is_connected:
        await _join(ctx)
    
    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

    if not url_rx.match(query):
        query = f'ytsearch:{query}'

    results = await player.node.get_tracks(query)

    if not results or not results.tracks:
        return await ctx.respond(':warning: No result for query!')
    
    embed = hikari.Embed(color=0x76ffa1)

    # Valid loadTypes are:
    #   TRACK_LOADED    - single video/direct URL)
    #   PLAYLIST_LOADED - direct URL to playlist)
    #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
    #   NO_MATCHES      - query yielded no results
    #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
    if results.load_type == 'PLAYLIST_LOADED':
        tracks = results.tracks

        for track in tracks:
            # Add all of the tracks from the playlist to the queue.
            player.add(requester=ctx.author.id, track=track)

        embed.description = f"Playlist '{results.playlist_info.name}' ({len(tracks)} added to queue [{ctx.author.mention}])"
    else:
        track = results.tracks[0]
        embed.description = f"[{track.title}]({track.uri}) added to queue [{ctx.author.mention}]"

        player.add(requester=ctx.author.id, track=track)

    await ctx.respond(embed=embed)

    if not player.is_playing:
        await player.play()
    else:
        logging.info("Track(s) enqueued on guild: %s", ctx.guild_id)
    

@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option("query", "The query to search for.", modifier=lightbulb.OptionModifier.CONSUME_REST, required=True)
@lightbulb.command("play", "Searches the query on youtube, or adds the URL to the queue.", auto_defer = True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def play(ctx: lightbulb.Context) -> None:
    """Searches the query on youtube, or adds the URL to the queue."""

    query = ctx.options.query
    await _play(query)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("leave", "Leaves the voice channel the bot is in, clearing the queue.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def leave(ctx: lightbulb.Context) -> None:
    """Leaves the voice channel the bot is in, clearing the queue."""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

    if not player.is_connected:
        await ctx.respond(":warning: Bot is not currently in any voice channel!")
        return

    player.queue.clear()  # clear queue
    await player.stop()  # stop player
    await plugin.bot.update_voice_state(ctx.guild_id, None) # disconnect from voice channel
    
    await ctx.respond("Left voice channel")


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("join", "Joins the voice channel you are in.")
@lightbulb.implements(lightbulb.SlashCommand)
async def join(ctx: lightbulb.Context) -> None:
    channel_id = await _join(ctx)

    if channel_id:
        await ctx.respond(f"Joined <#{channel_id}>")


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("stop", "Stops the current song and clears queue.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def stop(ctx: lightbulb.Context) -> None:
    """Stops the current song (skip to continue)."""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    
    if not player:
        await ctx.respond(":warning: Nothing to stop")
        return 
    
    player.queue.clear()
    await player.stop()

    await ctx.respond(
        embed = hikari.Embed(
            description = ":stop_button: Stopped playing",
            colour = 0xd25557
        )
    )

@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("skip", "Skips the current song.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def skip(ctx: lightbulb.Context) -> None:
    """Skips the current song."""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

    if not player or not player.is_playing:
        await ctx.respond(":warning: Nothing to skip")
    else:
        cur_track = player.current
        await player.play()

        await ctx.respond(
            embed = hikari.Embed(
                description = f":fast_forward: Skipped: [{cur_track.title}]({cur_track.uri})",
                colour = 0xd25557
            )
        )

@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("pause", "Pauses the current song.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def pause(ctx: lightbulb.Context) -> None:
    """Pauses the current song."""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

    if not player or not player.is_playing:
        await ctx.respond(":warning: Player is not currently playing!")
        return
    await player.set_pause(True)
    await ctx.respond(
        embed = hikari.Embed(
            description = ":pause_button: Paused player",
            colour = 0xf9c62b
        )
    )

@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("resume", "Resumes playing the current song.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def resume(ctx: lightbulb.Context) -> None:
    """Resumes playing the current song."""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if player and player.paused:
        await player.set_pause(False)
    else:
        await ctx.respond(":warning: Player is not currently paused!")
        return

    await ctx.respond(
        embed = hikari.Embed(
            description = ":arrow_forward: Resumed player",
            colour = 0x76ffa1
        )
    )

@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("queue", "Shows the next 10 songs in the queue", aliases = ['q'])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def queue(ctx : lightbulb.Context) -> None:

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

    if not player or not player.is_playing:
        await ctx.respond(":warning: Player is not currently playing")
        return 
    
    length = divmod(player.current.duration, 60000)
    queueDescription = f"**Current:** [{player.current.title}]({player.current.uri}) `{int(length[0])}:{round(length[1]/1000):02}` [<@!{player.current.requester}>]"
    i = 0
    while i < len(player.queue) and i < 10:
        if i == 0: 
            queueDescription += '\n\n' + '**Up next:**'
        length = divmod(player.queue[i].duration, 60000)
        queueDescription = queueDescription + '\n' + f"[{i + 1}. {player.queue[i].title}]({player.queue[i].uri}) `{int(length[0])}:{round(length[1]/1000):02}` [<@!{player.queue[i].requester}>]"
        i += 1

    queueEmbed = hikari.Embed(
        title = "🎶 Queue",
        description = queueDescription,
        colour = 0x76ffa1,
    )

    await ctx.respond(embed=queueEmbed)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("chill", "Play random linhnhichill", auto_defer = True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def chill(ctx: lightbulb.Context) -> None:

    BASE_YT_URL = 'https://www.youtube.com/watch'
    query = None

    rand_vid = -1
    next_page_token = None
    while True:
        res = plugin.bot.d.youtube.playlistItems().list(
            playlistId='PL-F2EKRbzrNS0mQqAW6tt75FTgf4j5gjS',  # linhnhichill's playlist ID
            part='snippet',
            pageToken = next_page_token,
            maxResults=50
        ).execute()

        if rand_vid == -1:
            rand_vid = random.randint(0, res['pageInfo']['totalResults'])
        if rand_vid < 50:
            vid_id = res['items'][rand_vid]['snippet']['resourceId']['videoId']  # id
            query = f"{BASE_YT_URL}?v={vid_id}" 
            break

        rand_vid -= 50
        next_page_token = res.get('nextPageToken')

    assert query is not None
    await _play(ctx, query)


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

    lavalink_data = {
        't': 'VOICE_STATE_UPDATE',
        'd': {
            'guild_id': event.state.guild_id,
            'user_id': event.state.user_id,
            'channel_id': event.state.channel_id,
            'session_id': event.state.session_id,
        }
    }

    await plugin.bot.d.lavalink.voice_update_handler(lavalink_data)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
