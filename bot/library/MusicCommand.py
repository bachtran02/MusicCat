import re
import hikari
import logging

from bot.utils import MusicCommandError
from bot.logger import track_logger

url_rx = re.compile(r'https?://(?:www\.)?.+')

class MusicCommand:
    
    def __init__(self, bot) -> None:
        self.bot = bot
    
    # async def _join(self, ctx: lightbulb.Context) -> Optional[hikari.Snowflake]:
    async def _join(self, guild_id, author_id):
        assert guild_id is not None

        states = self.bot.cache.get_voice_states_view_for_guild(guild_id)

        voice_state = [state[1] for state in filter(lambda i : i[0] == author_id, states.items())]
        bot_voice_state = [state[1] for state in filter(lambda i: i[0] == self.bot.get_me().id, states.items())]

        if not voice_state:
            raise MusicCommandError(":warning: Connect to a voice channel first!")

        channel_id = voice_state[0].channel_id

        if bot_voice_state:
            if channel_id != bot_voice_state[0].channel_id:
                raise MusicCommandError(":warning: I am already playing in another Voice Channel!")
        try:
            await self.bot.update_voice_state(guild_id, channel_id, self_deaf=True)
            self.bot.d.lavalink.player_manager.create(guild_id=guild_id)  
        except TimeoutError:
            raise MusicCommandError(":warning: I was unable to connect to the voice channel, maybe missing permissions? or some internal issue.")
        
        logging.info("Client connected to voice channel on guild: %s", guild_id)
        return channel_id
    
    async def _play(self, guild_id, author_id, query: str):
        assert guild_id is not None 

        query = query.strip('<>')
        player = self.bot.d.lavalink.player_manager.get(guild_id)

        if not player or not player.is_connected:
            await self._join(guild_id, author_id)
        
        player = self.bot.d.lavalink.player_manager.get(guild_id)

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)

        if not results or not results.tracks:
            # return await ctx.respond(':warning: No result for query!')
            raise MusicCommandError(":warning: No result for query!")
        
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
                player.add(requester=author_id, track=track)
                track_logger.info("%s - %s (%s)", track.title, track.author, track.uri)

            embed.description = f"Playlist '{results.playlist_info.name}' ({len(tracks)} added to queue [{author_id}])"
        else:
            track = results.tracks[0]
            embed.description = f"[{track.title}]({track.uri}) added to queue [<@{author_id}>]"

            player.add(requester=author_id, track=track)
            track_logger.info("%s - %s - %s", track.title, track.author, track.uri)

        if not player.is_playing:
            await player.play()
        else:
            logging.info("Track(s) enqueued on guild: %s", guild_id)

        return embed

    async def _leave(self, guild_id: str):

        player = self.bot.d.lavalink.player_manager.get(guild_id)

        if not player or not player.is_connected:
            raise MusicCommandError(":warning: Bot is not currently in any voice channel!")

        player.queue.clear()  # clear queue
        await player.stop()  # stop player
        await self.bot.update_voice_state(guild_id, None) # disconnect from voice channel
        
        logging.info("Bot disconnected from voice on guild: %s", guild_id)
    
    async def _stop(self, guild_id):

        player = self.bot.d.lavalink.player_manager.get(guild_id)
    
        if not player:
            raise MusicCommandError(":warning: Nothing to stop")
            
        player.queue.clear()
        await player.stop()

        logging.info("Player stopped on guild: %s", guild_id)

        return hikari.Embed(
            description = ":stop_button: Stopped playing",
            colour = 0xd25557
        )
    
    async def _skip(self, guild_id):
        player = self.bot.d.lavalink.player_manager.get(guild_id)

        if not player or not player.is_playing:
            raise MusicCommandError(":warning: Nothing to skip")

        cur_track = player.current
        await player.play()

        logging.info("Track skipped on guild: %s", guild_id)

        return hikari.Embed(
            description = f":fast_forward: Skipped: [{cur_track.title}]({cur_track.uri})",
            colour = 0xd25557
        )
    
    async def _pause(self, guild_id):
        player = self.bot.d.lavalink.player_manager.get(guild_id)

        if not player or not player.is_playing:
            raise MusicCommandError(":warning: Player is not currently playing!")
           
        await player.set_pause(True)

        logging.info("Track paused on guild: %s", guild_id)
        
        return hikari.Embed(
            description = ":pause_button: Paused player",
            colour = 0xf9c62b
        )
    
    async def _resume(self, guild_id):
        player = self.bot.d.lavalink.player_manager.get(guild_id)
        
        if player and player.paused:
            await player.set_pause(False)
        else:
            raise MusicCommandError(":warning: Player is not currently paused!")

        logging.info("Track resumed on guild: %s", guild_id)

        return hikari.Embed(
            description = ":arrow_forward: Resumed player",
            colour = 0x76ffa1
        )
    
    async def _queue(self, guild_id):
        player = self.bot.d.lavalink.player_manager.get(guild_id)

        if not player or not player.is_playing:
            raise MusicCommandError(":warning: Player is not currently playing")
        
        length = divmod(player.current.duration, 60000)
        queueDescription = f"**Current:** [{player.current.title}]({player.current.uri}) `{int(length[0])}:{round(length[1]/1000):02}` [<@!{player.current.requester}>]"
        i = 0
        while i < len(player.queue) and i < 10:
            if i == 0: 
                queueDescription += '\n\n' + '**Up next:**'
            length = divmod(player.queue[i].duration, 60000)
            queueDescription = queueDescription + '\n' + f"[{i + 1}. {player.queue[i].title}]({player.queue[i].uri}) `{int(length[0])}:{round(length[1]/1000):02}` [<@!{player.queue[i].requester}>]"
            i += 1

        return hikari.Embed(
            title = "🎶 Queue",
            description = queueDescription,
            colour = 0x76ffa1,
        )