import re
import hikari
import logging
import lightbulb
from typing import Optional

url_rx = re.compile(r'https?://(?:www\.)?.+')

class MusicClient:
    
    def __init__(self, plugin) -> None:
        self.plugin = plugin
    
    async def _join(self, ctx: lightbulb.Context) -> Optional[hikari.Snowflake]:
        assert ctx.guild_id is not None

        states = self.plugin.bot.cache.get_voice_states_view_for_guild(ctx.guild_id)

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
            await self.plugin.bot.update_voice_state(ctx.guild_id, channel_id, self_deaf=True)
            self.plugin.bot.d.lavalink.player_manager.create(guild_id=ctx.guild_id)  
        except TimeoutError:
            await ctx.respond(":warning: I was unable to connect to the voice channel, maybe missing permissions? or some internal issue.")
            return None
        
        logging.info("Client connected to voice channel on guild: %s", ctx.guild_id)
        return channel_id
    
    async def _play(self, ctx: lightbulb.Context, query: str):
        assert ctx.guild_id is not None 

        query = query.strip('<>')
        player = self.plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

        if not player or not player.is_connected:
            await self._join(ctx)
        
        player = self.plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

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

    async def _leave(self, guild_id: str):

        player = self.plugin.bot.d.lavalink.player_manager.get(guild_id)

        if not player or not player.is_connected:
            return False

        player.queue.clear()  # clear queue
        await player.stop()  # stop player
        await self.plugin.bot.update_voice_state(guild_id, None) # disconnect from voice channel
        
        logging.info("Bot disconnected from voice on guild: %s", guild_id)
        return True