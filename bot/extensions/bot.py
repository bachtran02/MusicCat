import hikari
import lightbulb

from bot.impl import _join
from bot.checks import valid_user_voice, player_connected
from bot.library.events import VoiceServerUpdate, VoiceStateUpdate

DELETE_AFTER = 60
plugin = lightbulb.Plugin('Bot', 'Bot commands')

"""
@plugin.command()
@lightbulb.command('ping', 'Test command')
@lightbulb.implements(lightbulb.SlashCommand)
async def ping(ctx: lightbulb.Context) -> None:
    await ctx.respond('pong!', flags=hikari.MessageFlag.EPHEMERAL)
"""

@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command('join', 'Join the voice channel you are in')
@lightbulb.implements(lightbulb.SlashCommand)
async def join(ctx: lightbulb.Context) -> None:
    """Join voice channel user is in"""
   
    try:
        player = await _join(plugin.bot, ctx.guild_id, ctx.author.id)
    except RuntimeError as e:
        await ctx.respond(e, flags=hikari.MessageFlag.EPHEMERAL)
    else:
        await ctx.respond(f'Joined <#{player.channel_id}>', delete_after=DELETE_AFTER)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_connected,
)
@lightbulb.command('leave', 'Leaves the voice channel the bot is in, clearing the queue')
@lightbulb.implements(lightbulb.SlashCommand)
async def leave(ctx: lightbulb.Context) -> None:
    """Leave voice channel, clear guild player"""

    await plugin.bot.update_voice_state(ctx.guild_id, None)
    await ctx.respond('Left voice channel!', delete_after=DELETE_AFTER)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command('mute', 'Disable sending message on track start')
@lightbulb.implements(lightbulb.SlashCommand)
async def mute(ctx: lightbulb.Context) -> None:
    """Disable sending message on track start"""

    plugin.bot.d.guilds[ctx.guild_id]['muted'] = True
    await ctx.respond('Bot muted!', delete_after=DELETE_AFTER)


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command('unmute', 'Enable sending message on track start')
@lightbulb.implements(lightbulb.SlashCommand)
async def unmute(ctx: lightbulb.Context) -> None:
    """Enable sending message on track start"""

    plugin.bot.d.guilds[ctx.guild_id]['muted'] = False
    await ctx.respond('Bot unmuted!', delete_after=DELETE_AFTER)


@plugin.listener(hikari.VoiceServerUpdateEvent)
async def voice_server_update(event: hikari.VoiceServerUpdateEvent) -> None:
    await plugin.bot.d.lavalink._dispatch_event(VoiceServerUpdate(event))

@plugin.listener(hikari.VoiceStateUpdateEvent)
async def voice_state_update(event: hikari.VoiceStateUpdateEvent) -> None:
    await plugin.bot.d.lavalink._dispatch_event(VoiceStateUpdate(event))


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
