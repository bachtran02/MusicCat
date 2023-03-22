import re
import hikari
import logging
import random
from requests import HTTPError

from bot.utils import get_spotify_playlist_id, duration_str
from bot.constants import COLOR_DICT, BASE_YT_URL, PLAYER_STORE_INIT

class MusicCommandError(Exception):
    """Raised when there is an error while calling a method in MusicCommand"""

class MusicCommand:
    
    def __init__(self, bot) -> None:
        self.bot = bot

    async def join(self, guild_id, author_id):
        assert guild_id is not None

        states = self.bot.cache.get_voice_states_view_for_guild(guild_id)
        voice_state = [state[1] for state in filter(lambda i : i[0] == author_id, states.items())]
        channel_id = voice_state[0].channel_id

        try:
            await self.bot.update_voice_state(guild_id, channel_id, self_deaf=True)
            player = self.bot.d.lavalink.player_manager.create(guild_id=guild_id)
            # initialize store
            player.store = PLAYER_STORE_INIT
        except TimeoutError as error:
            raise TimeoutError('Unable to connect to the voice channel!') from error
        
        logging.info('Client connected to voice channel on guild: %s', guild_id)
        return channel_id
    
    async def play(
            self, guild_id, author_id, query,
            channel_id=None, loop=False, autoplay=None, index=None,
        ):
    
        assert guild_id is not None

        player = self.bot.d.lavalink.player_manager.get(guild_id)
        if not player or not player.is_connected:
            await self.join(guild_id, author_id)
            player = self.bot.d.lavalink.player_manager.get(guild_id)

        query_type = ''
        embed = hikari.Embed(color=COLOR_DICT['GREEN'])
        
        if (not isinstance(player.store, dict)) or autoplay:
            use_autoplay = autoplay == 'True'
        else:
            use_autoplay = player.store['autoplay']
        
        player.store['autoplay'] = use_autoplay
        player.store['channel_id'] = channel_id

        query = query.strip('<>')  # to suppress embed on Discord 
        playlist_id = get_spotify_playlist_id(query)
        if playlist_id:  # Spotify Playlist
            if not self.bot.d.spotify:
                logging.warning('Failed to connect with Spotify API client! Check Spotify credentials')
                raise MusicCommandError('Failed to extract Spotify playlist!')
            try:
                playlist = self.bot.d.spotify.get_playlist_tracks(playlist_id)
            except HTTPError as error:
                logging.warning(error)
                raise MusicCommandError('Failed to retrieve playlist due to "%s"', error)
            
            for track in playlist['tracks']:
                squery = f'ytsearch:{track} audio'  # to avoid playing MV (may not work)
                results = await player.node.get_tracks(squery)

                if not results or not results.tracks:
                    logging.error('Track not found - lavalink search query: %s', squery)
                    continue

                track = results.tracks[0]
                player.add(requester=author_id, track=track)
            
            embed.description = f'Playlist [{playlist["name"]}]({query}) - {len(playlist["tracks"])} tracks added to queue <@{author_id}>'
            query_type = 'PLAYLIST'
        else:  # track name | track url | playlist url
            url_rx = re.compile(r'https?://(?:www\.)?.+')
            if not url_rx.match(query):
                query = f'ytsearch:{query}'

            results = await player.node.get_tracks(query)

            if not results or not results.tracks:
                raise MusicCommandError('No result for query!')

            if results.load_type == 'PLAYLIST_LOADED':  # YouTube playlist
                tracks = results.tracks
                for track in tracks:
                    # Add all of the tracks from the playlist to the queue.
                    player.add(requester=author_id, track=track)

                embed.description = f'Playlist [{results.playlist_info.name}]({query}) - {len(tracks)} tracks added to queue <@{author_id}>'
                query_type = 'PLAYLIST'
            else:   # 'SEARCH_RESULT' OR 'TRACK_LOADED'
                track = results.tracks[0]
                player.add(requester=author_id, track=track, index=index)
                embed.description = f'[{track.title}]({track.uri}) added to queue <@{author_id}>'
                query_type = 'TRACK'
                
        if not player.is_playing:
            await player.play()
            if loop:
                player.set_loop(1 if query_type=='TRACK' else 2) # loop track if single track is added
        return embed
    
    async def autoplay(self, guild_id):

        player = self.bot.d.lavalink.player_manager.get(guild_id)
        
        botid = self.bot.get_me().id
        embed = hikari.Embed(color=COLOR_DICT['GREEN'])
        last_track = player.store['last_played']
        
        search = self.bot.d.youtube.search().list(
            part='snippet',
            type='video',
            relatedToVideoId=last_track.identifier,
            maxResults=10
        ).execute()

        if not search['items']:
            raise MusicCommandError('No result for query!')

        items = search['items']
        top_items = items[:len(items)//2]
        random.shuffle(top_items)

        for item in top_items + items[len(items)//2:]:
            yid = item['id']['videoId']
            trackurl = f'{BASE_YT_URL}/watch?v={yid}'

            results = await player.node.get_tracks(trackurl)
            if not results or not results.tracks:
                raise MusicCommandError('No result for query!')
            
            track = results.tracks[0]
            if last_track.duration < 600000 and track.duration > 600000:
                continue

            track.requester = botid
            await player.play(track=track, no_replace=True)
            embed.description = f'[{track.title}]({track.uri}) added to queue <@{botid}>'
            break

        return [embed, player.store['channel_id']]

    async def leave(self, guild_id: str):

        player = self.bot.d.lavalink.player_manager.get(guild_id)
        player.store = PLAYER_STORE_INIT
        player.queue.clear()  # clear queue
        player.channel_id = None
        await player.stop()  # stop player
        await self.bot.update_presence(activity=None) # clear presence
        await self.bot.update_voice_state(guild_id, None) # disconnect from voice channel
        
        logging.info('Client disconnected from voice on guild: %s', guild_id)
    
    async def stop(self, guild_id):

        player = self.bot.d.lavalink.player_manager.get(guild_id)
        player.store = PLAYER_STORE_INIT
        player.set_loop(0)  # end any loop
        player.set_shuffle(False)  # disable shuffle
        player.queue.clear()
        await player.stop()
        await self.bot.update_presence(activity=None) # clear presence
        logging.info('Player stopped on guild: %s', guild_id)

        return hikari.Embed(
            description = '⏹️ Stopped playing',
            colour = COLOR_DICT['RED']
        )
    
    async def skip(self, guild_id):

        player = self.bot.d.lavalink.player_manager.get(guild_id)
        cur_track = player.current
        await player.skip()
        logging.info('Track skipped on guild: %s', guild_id)

        return hikari.Embed(
            description = f'Skipped: [{cur_track.title}]({cur_track.uri})',
            colour = COLOR_DICT['RED']
        )
    
    async def pause(self, guild_id):

        player = self.bot.d.lavalink.player_manager.get(guild_id)
        await player.set_pause(True)
        logging.info('Track paused on guild: %s', guild_id)
        
        return hikari.Embed(
            description = '⏸️ Paused player',
            colour = COLOR_DICT['YELLOW']
        )
    
    async def resume(self, guild_id):
        
        player = self.bot.d.lavalink.player_manager.get(guild_id)
        await player.set_pause(False)
        logging.info('Track resumed on guild: %s', guild_id)

        return hikari.Embed(
            description = '▶️ Resumed player',
            colour = COLOR_DICT['GREEN']
        )
    
    async def seek(self, guild_id, pos):
        
        player = self.bot.d.lavalink.player_manager.get(guild_id)
        if not player.current.is_seekable:
            raise MusicCommandError('Current track is not seekable!')

        pos_rx = re.compile(r'\d+:\d{2}$')
        if not pos_rx.match(pos) or int(pos.split(':')[1]) >= 60:
            raise MusicCommandError('Invalid position!')
        
        minute, second = [int(x) for x in pos.split(':')]
        ms = minute * 60 * 1000 + second * 1000
        await player.seek(ms)

        return hikari.Embed(
            description = f'⏩ Player moved to `{minute}:{second:02}`',
            colour = COLOR_DICT['BLUE']
        )
    
    async def loop(self, guild_id, mode):
        
        player = self.bot.d.lavalink.player_manager.get(guild_id)
        
        if mode == 'track':
            player.set_loop(1)
            body = '🔂 Enable Track loop!'
        elif mode == 'queue':
            player.set_loop(2)
            body = '🔁 Enable Queue loop!'
        else:
            player.set_loop(0)
            body = '⏭️ Disable loop!'
        
        return hikari.Embed(
            description = body,
            colour = COLOR_DICT['BLUE']
        )
    
    async def shuffle(self, guild_id):
        
        player = self.bot.d.lavalink.player_manager.get(guild_id)
        player.set_shuffle(not player.shuffle)

        return hikari.Embed(
            description = f'🔀 {("Shuffle enabled" if player.shuffle else "Shuffle disabled")}',
            colour = COLOR_DICT['BLUE']
        )
    
    async def flip_autoplay(self, guild_id, channel_id):

        player = self.bot.d.lavalink.player_manager.get(guild_id)
        player.store['autoplay'] = not player.store['autoplay']
        if player.store['autoplay']:
             player.store['channel_id'] = channel_id

        return hikari.Embed(
            description = f'🔀 {("Autoplay enabled" if player.store["autoplay"] else "Autoplay disabled")}',
            colour = COLOR_DICT['BLUE']
        )
    
    async def queue(self, guild_id):
        
        player = self.bot.d.lavalink.player_manager.get(guild_id)
        loop_emj = ''
        if player.loop == player.LOOP_SINGLE:
            loop_emj = '🔂'
        elif player.loop == player.LOOP_QUEUE:
            loop_emj = '🔁'

        shuffle_emj = '🔀' if player.shuffle else ''

        if player.current.stream:
            playtime = 'LIVE'
        else:
            playtime = f'{duration_str(player.position)} | {duration_str(player.current.duration)}'

        queue_description = f'**Current:** [{player.current.title}]({player.current.uri}) '
        queue_description += f'`{playtime}` <@!{player.current.requester}>'
        for i in range(min(len(player.queue), 10)):
            if i == 0:
                queue_description += '\n\n' + '**Up next:**'
            track = player.queue[i]
            queue_description = queue_description + '\n' + f'[{i + 1}. {track.title}]({track.uri}) `{duration_str(track.duration)}` <@!{track.requester}>'

        return hikari.Embed(
            title = f'🎵 Queue {loop_emj} {shuffle_emj}',
            description = queue_description,
            colour = COLOR_DICT['GREEN']
        )
    