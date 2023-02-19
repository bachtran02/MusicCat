import os
import hikari
from hikari import Intents
import lightbulb

from bot.logger import bot_logging_config

bot = lightbulb.BotApp(
    os.environ["TOKEN"],
    intents=(Intents.GUILDS | Intents.GUILD_MESSAGES | Intents.GUILD_VOICE_STATES),
    help_slash_command=True,
    banner=None,
    logs=bot_logging_config,
)

# Extension
bot.load_extensions_from("./bot/extensions", must_exist=True)

def run() -> None:
    bot.run(
        activity = hikari.Activity(
            name=f"/play",
            type=hikari.ActivityType.LISTENING
    ))
