import re
import hikari
import logging
from requests import HTTPError

from bot.utils import MusicCommandError, get_spotify_playlist_id

class MusicCommandError(Exception):
    pass

class MusicCommand:
    
    def __init__(self, bot) -> None:
        self.bot = bot
    
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
            raise MusicCommandError(":warning: Unable to connect to the voice channel")
        
        logging.info("Client connected to voice channel on guild: %s", guild_id)
        return channel_id
    
    async def _play(self, guild_id, author_id, channel_id, query, loop=False, autoplay=False):
        assert guild_id is not None

        query_type = enumerate(['PLAYLIST', 'TRACK'])
        query = query.strip('<>')
        player = self.bot.d.lavalink.player_manager.get(guild_id)

        if not player or not player.is_connected:
            await self._join(guild_id, author_id)
        
        embed = hikari.Embed(color=0x76ffa1)
        player = self.bot.d.lavalink.player_manager.get(guild_id)
        
        player.store = {
            'autoplay': True if autoplay else False,
            'channel_id': channel_id,
            'requester': author_id,
            'last_played': None,
        }

        # if query is spotify playlist url
        playlist_id = get_spotify_playlist_id(query)
        if playlist_id:
            if not self.bot.d.spotify:
                logging.warning("Failed to connect with Spotify API client! Check Spotify credentials")
                raise MusicCommandError(":warning: Failed to extract Spotify playlist!")

            query_type = 'PLAYLIST'
            try:
                playlist = self.bot.d.spotify.get_playlist_tracks(playlist_id)
            except HTTPError as e:
                logging.warning(e)
                raise MusicCommandError("Playlist not found!")
            
            for track in playlist['tracks']:
                squery = f'ytsearch:{track} lyrics'  # to avoid playing MV (may not work)
                results = await player.node.get_tracks(squery)

                if not results or not results.tracks:
                    logging.error("Track not found - lavalink search query: %s", squery)
                    continue

                track = results.tracks[0]
                player.add(requester=author_id, track=track)
            
            embed.description = f'Playlist [{playlist["name"]}]({query}) - {len(playlist["tracks"])} tracks added to queue [<@{author_id}>]'
        else:
            url_rx = re.compile(r'https?://(?:www\.)?.+')
            if not url_rx.match(query):
                query = f'ytsearch:{query}'

            results = await player.node.get_tracks(query)

            if not results or not results.tracks:
                raise MusicCommandError(":warning: No result for query!")

            if results.load_type == 'PLAYLIST_LOADED':  # Youtube playlist
                query_type = 'PLAYLIST'
                tracks = results.tracks
        
                for track in tracks:
                    # Add all of the tracks from the playlist to the queue.
                    player.add(requester=author_id, track=track)

                embed.description = f'Playlist [{results.playlist_info.name}]({query}) - {len(tracks)} tracks added to queue [<@{author_id}>]'
            else:   # 'SEARCH_RESULT' OR 'TRACK_LOADED'
                query_type = 'TRACK'
                track = results.tracks[0]
                embed.description = f"[{track.title}]({track.uri}) added to queue [<@{author_id}>]"

                player.add(requester=author_id, track=track)

        if not player.is_playing:
            await player.play()
            if loop:
                if query_type == 'PLAYLIST':
                    player.set_loop(2)
                else:
                    player.set_loop(1)
        else:
            logging.info("Track(s) enqueued on guild: %s", guild_id)
            if loop:
                raise MusicCommandError("Track(s) added to queue! Cannot enable loop for track(s) that are on queue!")
            
        return embed

    async def _leave(self, guild_id: str):

        player = self.bot.d.lavalink.player_manager.get(guild_id)

        if not player or not player.is_connected:
            raise MusicCommandError(":warning: Bot is not currently in any voice channel!")

        player.store = {
            'autoplay': False,
            'channel_id': None,
            'requester': None,
            'last_played': None,
        }

        player.queue.clear()  # clear queue
        await player.stop()  # stop player
        await self.bot.update_voice_state(guild_id, None) # disconnect from voice channel
        
        logging.info("Bot disconnected from voice on guild: %s", guild_id)
    
    async def _stop(self, guild_id):

        player = self.bot.d.lavalink.player_manager.get(guild_id)

        if not player:
            raise MusicCommandError(":warning: Nothing to stop")
        
        player.store = {
            'autoplay': False,
            'channel_id': None,
            'requester': None,
            'last_played': None,
        }

        player.queue.clear()
        await player.stop()
        # end loop and disable shuffle
        player.set_loop(0)
        player.set_shuffle(False)

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
    
    async def _seek(self, guild_id, pos):
        player = self.bot.d.lavalink.player_manager.get(guild_id)
        
        if not player or not player.is_playing:
            raise MusicCommandError(":warning: Player is not currently playing!")

        pos_rx = re.compile(r'\d+:\d{2}$')
        if not pos_rx.match(pos):
            raise MusicCommandError(":warning: Invalid position!")
        
        m, s = [int(x) for x in pos.split(':')]

        if s >= 60:
            raise MusicCommand(":warning: Invalid position!")

        ms = m * 60 * 1000 + s * 1000
        await player.seek(ms)

        return hikari.Embed(
            description = f":fast_forward: Player moved to `{m}:{s:02}`",
            colour = 0x76ffa1
        )
    
    async def _loop(self, guild_id, mode):
        player = self.bot.d.lavalink.player_manager.get(guild_id)
        
        if not player or not player.is_playing:
            raise MusicCommandError(":warning: Player is not currently playing!")
        
        body = ""
        if mode == 'end':
            player.set_loop(0)
            body = ":track_next: Disable loop!"
        if mode == 'track':
            player.set_loop(1)
            body = f":repeat_one: Enable Track loop!"
        if mode == 'queue':
            player.set_loop(2)
            body = f":repeat: Enable Queue loop!"
        
        return hikari.Embed(
            description = body,
            colour = 0xf0f8ff
        )
    
    async def _shuffle(self, guild_id):
        player = self.bot.d.lavalink.player_manager.get(guild_id)
        
        if not player or not player.is_playing:
            raise MusicCommandError(":warning: Player is not currently playing!")
        
        player.set_shuffle(not player.shuffle)

        return hikari.Embed(
            description = ":twisted_rightwards_arrows: " + ("Shuffle enabled" if player.shuffle else "Shuffle disabled"),
            colour = 0xf0f8ff
        )
    
    async def _queue(self, guild_id):
        player = self.bot.d.lavalink.player_manager.get(guild_id)

        if not player or not player.is_playing:
            raise MusicCommandError(":warning: Player is not currently playing")

        emj = {
            player.LOOP_SINGLE: ':repeat_one:',
            player.LOOP_QUEUE: ':repeat:',
        }

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
            title = f":musical_note: Queue {emj.get(player.loop, '')} {':twisted_rightwards_arrows:' if player.shuffle else ''}",
            description = queueDescription,
            colour = 0x76ffa1,
        )