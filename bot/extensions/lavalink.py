import hikari
import lightbulb

from bot.utils import format_time
from bot.constants import COLOR_DICT

plugin = lightbulb.Plugin('Lavalink', 'Lavalink commands')


@plugin.command()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command('stats', 'Display lavalink stats')
@lightbulb.implements(lightbulb.SlashCommand)
async def stats(ctx: lightbulb.Context) -> None:
    """Display lavalink stats."""

    node_manager = plugin.bot.d.lavalink.node_manager
    body = '**Nodes:**' + '\n'
    for i, node in enumerate(node_manager.nodes):
        body += '{}. `{} []`\n'.format(i + 1, node.name, node.region)
    body += '\n**Lavalink Stats:**\n'

    if node_manager.nodes and (stats := node_manager.nodes[0].stats) and not stats.is_fake:
        body += 'Uptime: `{}`\nPlayers: `{} ({} playing)`\nMemory: `{} MB ({}%)`\n \
            Lavalink load: `{}%`\nSystem load: `{}%`\nFrames sent: `{}`\n'.format(
                format_time(stats.uptime, "d"), 
                stats.players, stats.playing_players,
                round(stats.memory_used/1e6), round(100*stats.memory_used/stats.memory_allocated),
                round(stats.lavalink_load*100, 2), round(stats.system_load*100, 2), stats.frames_sent)
    else:
        body += 'No stats available' + '\n'

    await ctx.respond(embed=hikari.Embed(
        title = '📊 Lavalink Stats',
        description = body,
        colour = COLOR_DICT['BLUE']))


@plugin.command()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command('info', 'Display lavalink info')
@lightbulb.implements(lightbulb.SlashCommand)
async def info(ctx: lightbulb.Context) -> None:
    """Display lavalink info."""

    node_manager = plugin.bot.d.lavalink.node_manager
    if nodes := node_manager.nodes:
        body = ''
        info = await nodes[0].get_info()
        for item in info:
            body += '- {}: `{}`\n'.format(item, info[item])
    else:
        body = 'No info available' + '\n' 

    await ctx.respond(embed=hikari.Embed(
        title = '📊 Lavalink Info',
        description = body,
        colour = COLOR_DICT['BLUE']))


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
