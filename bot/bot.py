import os
import miru
import hikari
import lavalink
import lightbulb
import logging

from bot.event_handler import EventHandler
from bot.custom_sources import lnchillSource
from bot.library.player import CustomPlayer
from bot.logger.bot_logger import bot_logging_config

bot = lightbulb.BotApp(
    os.environ['TOKEN'],
    intents=(hikari.Intents.GUILDS | hikari.Intents.GUILD_VOICE_STATES),
    help_slash_command=True, banner=None,
    logs=bot_logging_config,
)

# load extension
bot.load_extensions_from('./bot/extensions', must_exist=True)

# on bot bot ready, add lavalink node to datastore
@bot.listen(hikari.StartedEvent)
async def on_started_event(event: hikari.StartedEvent) -> None:
    nodes = [
            {'name': 'default-node',  'region': 'us-west'},
            {'name': 'backup-node', 'region': 'us'}
        ]
    sources = [  lnchillSource(token=os.environ['YOUTUBE_API_KEY']),  ]

    client = lavalink.Client(user_id=bot.get_me().id, player=CustomPlayer)
    
    for node in nodes:
        client.add_node(
            host='localhost', port=2333,
            password=os.environ['LAVALINK_PASS'],
            region=node['region'], name=node['name'],
        )
    for source in sources:
        client.register_source(source)
        logging.info('Registred \'%s\' as source', source.name)

    client.add_event_hooks(EventHandler(event.app))
    bot.d.lavalink = client

def run() -> None:
    miru.install(bot)
    bot.run()

