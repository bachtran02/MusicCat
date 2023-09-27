import os
import miru
import hikari
import lavalink
import lightbulb
import logging

from bot.nodes import LAVALINK_NODES
from bot.event_handler import EventHandler
from bot.library.datastore import BotDataStore
from bot.library.player import CustomPlayer
from bot.logger.bot_logger import bot_logging_config
from bot.logger.custom_logger import command_logger

bot = lightbulb.BotApp(
    os.environ['TOKEN'],
    intents=(hikari.Intents.GUILDS | hikari.Intents.GUILD_VOICE_STATES),
    help_slash_command=True, banner=None,
    logs=bot_logging_config,
)

bot.load_extensions_from('./bot/extensions', must_exist=True)

@bot.listen(hikari.StartedEvent)
async def on_started_event(event: hikari.StartedEvent) -> None:
    
    client = lavalink.Client(user_id=bot.get_me().id, player=CustomPlayer)
    for node in LAVALINK_NODES:
        client.add_node(
            host='lavalink', port=2333,
            password=os.environ['LAVALINK_PASS'],
            region=node.get('region'), name=node['name'],
        )
    client.add_event_hooks(EventHandler(event.app))
    bot.d = BotDataStore(lavalink=client).to_datastore()

@bot.listen(lightbulb.CommandInvocationEvent)
async def on_command(event: lightbulb.CommandInvocationEvent) -> None:
    command_logger.info('\'/%s\' invocated by \'%s\' on guild: %d', 
        event.command.name, event.context.author.username,event.context.guild_id)
    
# @bot.listen(lightbulb.CommandInvocationError)
# async def on_command_error(event):
#     pass

@bot.listen(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:

    exception = event.exception
    if isinstance(exception, lightbulb.CheckFailure):
        causes = exception.causes or [exception]
        error_msg = causes[0]
        errors = [cause.__class__.__name__ for cause in causes]
        logging.error('%s errors on guild %s', errors, event.context.guild_id)   
    else:
        raise exception
    await event.context.respond(error_msg, flags=hikari.MessageFlag.EPHEMERAL)
    

def run() -> None:
    miru.install(bot)
    bot.run()
