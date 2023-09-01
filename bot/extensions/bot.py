import hikari
import lightbulb

from bot.impl import _join
from bot.checks import valid_user_voice, player_connected
from bot.library.events import VoiceServerUpdate, VoiceStateUpdate

plugin = lightbulb.Plugin('Bot', 'Bot commands')


@plugin.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command('join', 'Join the voice channel you are in.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def join(ctx: lightbulb.Context) -> None:
    """Join voice channel user is in"""
   
    try:
        player = await _join(plugin.bot, ctx.guild_id, ctx.author.id)
    except RuntimeError as error:
        await ctx.respond(f'⚠️ {error}')
    else:
        await ctx.respond(f'Joined <#{player.channel_id}>')


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_connected,
)
@lightbulb.command('leave', 'Leaves the voice channel the bot is in, clearing the queue.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def leave(ctx: lightbulb.Context) -> None:
    """Leave voice channel, clear guild player"""

    await plugin.bot.update_voice_state(ctx.guild_id, None)
    await ctx.respond('Left voice channel!')


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
