import os
import hikari
from hikari import Intents
import lightbulb
import miru

from bot.logger.bot_logger import bot_logging_config

bot = lightbulb.BotApp(
    os.environ['TOKEN'],
    intents=(Intents.GUILDS | Intents.GUILD_VOICE_STATES),
    help_slash_command=True, banner=None,
    logs=bot_logging_config,
)

# load extension
bot.load_extensions_from('./bot/extensions', must_exist=True)

def run() -> None:
    miru.install(bot) # Load miru and attach it to the bot instance.
    bot.run()

async def remove_command(guild_id=hikari.UNDEFINED):
    
    rest = hikari.RESTApp()
    await rest.start()
    
    client = rest.acquire(os.environ['TOKEN'], hikari.TokenType.BOT)
    application = await client.fetch_application()
    await client.set_application_commands(application.id, (), guild=guild_id)
