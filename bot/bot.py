import os
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
    miru.install(bot)
    bot.run()

