import logging

import hikari
import lavalink

from bot.constants import COLOR_DICT
from bot.library.events import VoiceServerUpdate, VoiceStateUpdate
from bot.library.player_view import PlayerView
from bot.logger.custom_logger import track_logger
from bot.utils import track_display, player_bar 

class EventHandler:
    """Events from the Lavalink server"""

    def __init__(self, bot) -> None:
        self.bot = bot

    @lavalink.listener(VoiceServerUpdate)
    async def voice_server_update(self, event: VoiceServerUpdate):

        await self.bot.d.lavalink.voice_update_handler({
        't': 'VOICE_SERVER_UPDATE',
        'd': {
            'guild_id': event.guild_id,
            'endpoint': event.endpoint,
            'token': event.token,
        }})

    @lavalink.listener(VoiceStateUpdate)
    async def voice_state_update(self, event: VoiceStateUpdate):
        
        await self.bot.d.lavalink.voice_update_handler({
        't': 'VOICE_STATE_UPDATE',
        'd': {
            'guild_id': event.cur_state.guild_id,
            'user_id': event.cur_state.user_id,
            'channel_id': event.cur_state.channel_id,
            'session_id': event.cur_state.session_id,
        }})
        await self.check_voice(event)

    @lavalink.listener(lavalink.TrackStartEvent)
    async def track_start(self, event: lavalink.TrackStartEvent):

        track, guild_id = event.track, event.player.guild_id
        track_logger.info('%s - %s - %s', track.title, track.author, track.uri)
        logging.info('Track started on guild: %s', guild_id)

        await self.update_player(event, guild_id) or await self.send_nowplaying(event, guild_id)

    @lavalink.listener(lavalink.TrackEndEvent)
    async def track_end(self, event: lavalink.TrackEndEvent):
        logging.info('Track finished on guild: %s', event.player.guild_id)

    @lavalink.listener(lavalink.QueueEndEvent)
    async def queue_finish(self, event: lavalink.QueueEndEvent):
        await self.update_player(event, event.player.guild_id)
        logging.info('Queue finished on guild: %s', event.player.guild_id)
        
    @lavalink.listener(lavalink.TrackExceptionEvent)
    async def track_exception(self, event: lavalink.TrackExceptionEvent):
        logging.warning('Track exception event happened on guild: %s', event.player.guild_id)

    async def check_voice(self, event: VoiceStateUpdate):
        
        bot_id = self.bot.get_me().id
        cur_state, prev_state = event.cur_state, event.prev_state
        user_id, guild_id = cur_state.user_id, cur_state.guild_id
        bot_state = self.bot.cache.get_voice_state(guild_id, bot_id)
        player = self.bot.d.lavalink.player_manager.get(guild_id)

        if not bot_state or user_id == bot_id:
            if not bot_state and user_id == bot_id:  # bot is disconnected
                await player.stop()
                logging.info('Client disconnected from voice on guild: %s', event.cur_state.guild_id)
            return

        # event occurs in channel not same as bot
        if not ((prev_state and prev_state.channel_id == bot_state.channel_id) or
            (cur_state and cur_state.channel_id == bot_state.channel_id)):
                return

        states = self.bot.cache.get_voice_states_view_for_guild(cur_state.guild_id).items()
        user_count = len([state[0] for state in filter(lambda x: x[1].channel_id == bot_state.channel_id, states)])  # count users in channel with bot

        if user_count != 2:  
            if user_count == 1:     # bot by itself in voice chat
                await self.bot.update_voice_state(cur_state.guild_id, None)
            return

        # resume player when user undeafens
        if prev_state.is_self_deafened and not cur_state.is_self_deafened:
            if player and player.paused:
                await player.set_pause(False)
                logging.info('Track resumed on guild: %s', guild_id)

        # pause player when user deafens
        if not prev_state.is_self_deafened and cur_state.is_self_deafened:
            if not player or not player.is_playing:
                return
            await player.set_pause(True)
            logging.info('Track paused on guild: %s', guild_id)

    async def send_nowplaying(self, event, guild_id):
        
        current = event.track
        channel_id = current.extra.get('channel_id')

        if channel_id and not self.bot.d.guilds.get(guild_id, {}).get('muted', False):
            if event.player.loop == lavalink.DefaultPlayer.LOOP_SINGLE:
                if self.bot.d.guilds.get(guild_id, {}).get('track_loop'):
                    return
                self.bot.d.guilds[guild_id]['track_loop'] = True
            else:
                self.bot.d.guilds[guild_id]['track_loop'] = False
            try:
                await self.bot.rest.create_message(
                    channel=channel_id,
                    embed=hikari.Embed(
                        title='**Now playing**',
                        description = '{} \n Requested - <@{}>\n'.format(
                            track_display(current), current.requester),
                        color = COLOR_DICT['GREEN'],
                    ).set_thumbnail(current.artwork_url))
            except Exception as error:
                logging.error('Failed to send message on track start due to: %s', error)

    async def update_player(self, event, guild_id):

        redis = self.bot.d.redis
        if not redis.exists(guild_id):
            return False
        
        message_id, channel_id = [int(i) for i in redis.hgetall(guild_id).values()]
        message = await self.bot.rest.fetch_message(channel_id, message_id)
        # TODO: handle different states of message
        await message.edit(embed=PlayerView.get_embed(event.player))
        return True