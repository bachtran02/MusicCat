import os
import redis
import logging

import hikari
import lavalink
import lightbulb
import miru

from bot.config import *
from bot.library.event_handler import EventHandler
from bot.library.mc_player import MusicCatPlayer
from bot.logger.bot_logger import bot_logging_config
from bot.logger.custom_logger import command_logger

bot = lightbulb.BotApp(
    os.environ['TOKEN'],
    intents=(hikari.Intents.GUILDS | hikari.Intents.GUILD_VOICE_STATES),
    help_slash_command=True, banner=None,
    logs=bot_logging_config,
)

bot.load_extensions_from('./bot/extensions', must_exist=True)

def setup_lavalink(client: lavalink.Client, event_handler: EventHandler, nodes=[{'name': 'node-1'}]):
    
    assert isinstance(client, lavalink.Client)

    client.add_event_hooks(event_handler)
    for node in nodes:
        client.add_node(
            host=LAVALINK_HOST, port=LAVALINK_PORT,
            password=LAVALINK_PASSWORD,
            region=node.get('region'), name=node['name'])

"""
async def setup_bot():

    redis = bot.d.redis
    if not redis.ping():    # check if connection to redis is ok
        raise ConnectionError('Failed to connect to Redis')
    
    async for guild in bot.rest.fetch_my_guilds():
        guild_id = guild.id
        bot.d.guilds[guild_id] = {'muted': False, 'track_loop': False}
        if redis.exists(guild_id):
            view = PlayerView()
            message_id, channel_id = [int(i) for i in redis.hgetall(guild_id).values()]
            message = await bot.rest.fetch_message(channel_id, message_id)
            # TODO: handle different message states
            await message.edit(components=viesw)
            await view.start(message)
"""

@bot.listen(hikari.StartedEvent)
async def on_started_event(event: hikari.StartedEvent) -> None:
    
    bot.d.lavalink = lavalink.Client(user_id=bot.get_me().id, player=MusicCatPlayer)
    setup_lavalink(bot.d.lavalink, EventHandler(event.app), LAVALINK_NODES)

@bot.listen(lightbulb.CommandInvocationEvent)
async def on_command(event: lightbulb.CommandInvocationEvent) -> None:
    command_logger.info('\'/%s\' invocated by \'%s\' on guild: %d', 
        event.command.name, event.context.author.username,event.context.guild_id)
    

@bot.listen(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:

    exception = event.exception
    if isinstance(exception, lightbulb.CheckFailure):
        causes = exception.causes or [exception]
        error_msg = causes[0]
        errors = [cause.__class__.__name__ for cause in causes]
        logging.error('%s errors on guild %s', errors, event.context.guild_id) 
    # elif isinstance(exception, lightbulb.CommandInvocationError):
    #     raise exception
    else:
        raise exception
    await event.context.respond(error_msg, flags=hikari.MessageFlag.EPHEMERAL)
    

def run() -> None:
    miru.install(bot)
    bot.run()
