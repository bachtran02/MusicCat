import os
import miru
import hikari
import lavalink
import lightbulb
import logging

from bot.nodes import LAVALINK_NODES
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
    
    sources = [  lnchillSource(token=os.environ['YOUTUBE_API_KEY']),  ]
    client = lavalink.Client(user_id=bot.get_me().id, player=CustomPlayer)
    
    for node in LAVALINK_NODES:
        client.add_node(
            host='lavalink', port=2333,  # use host='localhost' if bot is not run on docker
            password=os.environ['LAVALINK_PASS'],
            region=node.get('region'), name=node['name'],
        )
    for source in sources:
        client.register_source(source)
        logging.info('Registred \'%s\' as source', source.name)

    client.add_event_hooks(EventHandler(event.app))
    bot.d.lavalink = client

@bot.listen(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:

    exception = event.exception
    error_msg = ''

    if isinstance(exception, lightbulb.CheckFailure):
        if exception.causes:
            error_msg += f'Multiple check failures:\n'
            for cause in exception.causes:
                if isinstance(cause, lightbulb.CheckFailure):
                    error_msg += f'- `{cause}`\n'
        else:
            error_msg += f'{exception}\n'
    if isinstance(exception, lightbulb.OnlyInGuild):
        error_msg += f'Cannot invoke Guild only command in DMs\n'
    elif isinstance(exception, lightbulb.NotOwner):
        error_msg += f'Only bot owner can use this command\n'
    if not error_msg:   # if error is not handled
        logging.error(exception)
        raise exception
    await event.context.respond(error_msg)

def run() -> None:
    miru.install(bot)
    bot.run()
