import hikari
import lightbulb

from bot.utils import format_time
from bot.constants import COLOR_DICT

plugin = lightbulb.Plugin('Lavalink', 'Lavalink info')

@plugin.command()
# @lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command('stats', 'Display lavalink stats.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def stats(ctx: lightbulb.Context) -> None:
    """Display lavalink stats."""

    node_manager = plugin.bot.d.lavalink.node_manager
    body = '**Nodes:**' + '\n'
    for i, node in enumerate(node_manager.nodes):
        body += f'{i+1}. `{node.name} [{node.region}]`' + '\n'

    body += '\n' + '**Lavalink Stats:**' + '\n'
    if node_manager.nodes and (stats := node_manager.nodes[0].stats) and not stats.is_fake:
        body += f'Uptime: `{format_time(stats.uptime, "d")}`'+ '\n'
        body += f'Players: `{stats.players} ({stats.playing_players} playing)`' + '\n'
        body += f'Memory: `{round(stats.memory_used/1e6)} MB ({round(100*stats.memory_used/stats.memory_allocated)}%)`'  + '\n'
        body += f'Lavalink load: `{round(stats.lavalink_load*100, 2)}%`' + '\n'
        body += f'System load: `{round(stats.system_load*100, 2)}%`' + '\n'
        body += f'Frames sent: `{stats.frames_sent}`' + '\n'
    else:
        body += 'No stats available' + '\n'

    await ctx.respond(embed=hikari.Embed(
        title = '📊 Lavalink Stats',
        description = body,
        colour = COLOR_DICT['BLUE']))


@plugin.command()
# @lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command('info', 'Display lavalink info.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def info(ctx: lightbulb.Context) -> None:
    """Display lavalink info."""

    node_manager = plugin.bot.d.lavalink.node_manager
    if nodes := node_manager.nodes:
        body = ''
        info = await nodes[0].get_info()
        item_name = ['Version', 'Build Time', 'Git', 'JVM', 'Lavaplayer', 'Source Managers', 'Filters', 'Plugins']
        for i, item in enumerate(info):
            body += f'- {item_name[i]}: `{info[item]}`' + '\n'
    else:
        body = 'No info available' + '\n' 

    await ctx.respond(embed=hikari.Embed(
        title = '📊 Lavalink Info',
        description = body,
        colour = COLOR_DICT['BLUE']))

@plugin.set_error_handler
async def foo_error_handler(event: lightbulb.CommandErrorEvent) -> bool:
    if isinstance(event.exception, lightbulb.CommandInvocationError):
        await event.context.respond(f'Something went wrong during invocation of command `{event.context.command.name}`.')
        raise event.exception

    # Unwrap the exception to get the original cause
    exception = event.exception.__cause__ or event.exception
    if isinstance(exception, lightbulb.NotOwner):
        await event.context.respond('Only bot owner can use this command!')


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
