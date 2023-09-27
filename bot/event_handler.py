import logging
import hikari
import lavalink

from bot.library.events import VoiceServerUpdate, VoiceStateUpdate
from bot.constants import COLOR_DICT
from bot.utils import track_display 
from bot.logger.custom_logger import track_logger

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

        bot_id = self.bot.get_me().id
        bot_voice_state = self.bot.cache.get_voice_state(event.cur_state.guild_id, bot_id)
        player = self.bot.d.lavalink.player_manager.get(event.cur_state.guild_id)

        if not bot_voice_state or event.cur_state.user_id == bot_id:
            if not bot_voice_state and event.cur_state.user_id == bot_id:  # bot is disconnected
                await player.stop()
                self.bot.d.guilds.pop(event.cur_state.guild_id)
                logging.info('Client disconnected from voice on guild: %s', event.cur_state.guild_id)
            return

        # event occurs in channel not same as bot
        if not ((event.prev_state and event.prev_state.channel_id == bot_voice_state.channel_id) or
            (event.cur_state and event.cur_state.channel_id == bot_voice_state.channel_id)):
                return

        states = self.bot.cache.get_voice_states_view_for_guild(event.cur_state.guild_id).items()
        cnt_user = len([state[0] for state in filter(lambda i: i[1].channel_id == bot_voice_state.channel_id, states)])  # count users in channel with bot

        # TODO: doesn't resume if bot is not autopaused
        if cnt_user != 2:  
            if cnt_user == 1:
                await self.bot.update_voice_state(event.cur_state.guild_id, None)
            return

        # resume player when user undeafens
        if event.prev_state.is_self_deafened and not event.cur_state.is_self_deafened:
            if player and player.paused:
                await player.set_pause(False)
                logging.info('Track resumed on guild: %s', event.guild_id)

        # pause player when user deafens
        if not event.prev_state.is_self_deafened and event.cur_state.is_self_deafened:
            if not player or not player.is_playing:
                return
            await player.set_pause(True)
            logging.info('Track paused on guild: %s', event.guild_id)

    @lavalink.listener(lavalink.TrackStartEvent)
    async def track_start(self, event: lavalink.TrackStartEvent):

        track = event.track
        track_logger.info('%s - %s - %s', event.track.title, event.track.author, event.track.uri)
        logging.info('Track started on guild: %s', event.player.guild_id)
        
        data = self.bot.d.guilds[event.player.guild_id]
        if data.channel_id and data.send_nowplaying:
            if event.player.loop == 1:
                if not data.track_loop:
                    self.bot.d.guilds[event.player.guild_id].track_loop = True
                else: 
                    return
            else:
                self.bot.d.guilds[event.player.guild_id].track_loop = False
            
            try:
                await self.bot.rest.create_message(
                    channel=data.channel_id,
                    embed=hikari.Embed(
                        title='**Now playing**',
                        description = '{} \n Requested - <@{}>\n'.format(
                            track_display(track), track.requester),
                        color = COLOR_DICT['GREEN'],
                    ).set_thumbnail(track.artwork_url)
                )
            except Exception as error:
                logging.error('Failed to send message on track start due to: %s', error)

    @lavalink.listener(lavalink.TrackEndEvent)
    async def track_end(self, event: lavalink.TrackEndEvent):

        if not event.player.queue or event.track.identifier != event.player.queue[0].identifier:
            event.player.recently_played.append(event.track)

        logging.info('Track finished on guild: %s', event.player.guild_id)

    @lavalink.listener(lavalink.QueueEndEvent)
    async def queue_finish(self, event: lavalink.QueueEndEvent):
        logging.info('Queue finished on guild: %s', event.player.guild_id)
        
    @lavalink.listener(lavalink.TrackExceptionEvent)
    async def track_exception(self, event: lavalink.TrackExceptionEvent):
        logging.warning('Track exception event happened on guild: %s', event.player.guild_id)
