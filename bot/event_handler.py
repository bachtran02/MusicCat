import logging
import hikari
import lavalink

from bot.constants import COLOR_DICT
from bot.logger.custom_logger import track_logger

class EventHandler:
    """Events from the Lavalink server"""

    def __init__(self, bot) -> None:
        self.bot = bot
    
    @lavalink.listener(lavalink.TrackStartEvent)
    async def track_start(self, event: lavalink.TrackStartEvent):

        description  = '[{0}]({1})\n Requested - <@{2}>\n'.format(
            event.track.title, event.track.uri, event.track.requester)
        
        try:
            # await plugin.bot.rest.create_message(
            await self.bot.rest.create_message(
                channel=event.player.text_id,
                embed=hikari.Embed(
                    title='🎶 **Now playing**',
                    description = description,
                    colour = COLOR_DICT['GREEN'],
                ).set_thumbnail(event.track.artwork_url)
            )
        except Exception as error:
            logging.error('Failed to send message on track start due to: %s', error)

        track_logger.info('%s - %s - %s', event.track.title, event.track.author, event.track.uri)
        logging.info('Track started on guild: %s', event.player.guild_id)

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
